"""
    Get a loader this.

    This is the entry point to the api.

    The api handles all interaction with the external
    system.

    This handles our internals and relationship
    between elcid.

    we have 5 entry points

    initial_load()
    nukes all existing lab tests and replaces them.

    this is run in the inital load below. When we add a patient for the
    first time, when we add a patient who has demographics or when we've
    reconciled a patient.

    batch_load()
    Tries to reconcile all unreconciled demographics

    runs the batch load for all patients that are reconciled.
    currently not being loaded in.

    this is run every 5 mins and after deployments

    Loads everything since the start of the previous
    successful load so that we paper over any cracks.

    load_patient()
    is what is run when we run it from the admin, or
    after a patient has been reconciled from teh reconciliation pathway.
    It loads in data for a single specific patient.

    any_loads_running()
    returns true if any, ie initial or batch, loads are running
"""

import datetime
import traceback
import json
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from intrahospital_api import models
from elcid import models as emodels
from opal.models import Patient
from elcid.utils import timing
from intrahospital_api import get_api
from intrahospital_api.exceptions import BatchLoadError
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api import update_demographics
from intrahospital_api import update_lab_tests
from intrahospital_api import logger

api = get_api()


@timing
def initial_load():
    models.InitialPatientLoad.objects.all().delete()
    models.BatchPatientLoad.objects.all().delete()
    batch = models.BatchPatientLoad()
    batch.start()

    try:
        _initial_load()
    except:
        batch.failed()
        logger.error("Unable to run initial_load \n{}".format(
            traceback.format_exc()
        ))
        raise
    else:
        batch.complete()


def _initial_load():
    update_demographics.reconcile_all_demographics()
    # only run for reconciled patients
    patients = Patient.objects.filter(
        demographics__external_system=EXTERNAL_SYSTEM
    )
    total = patients.count()

    for iterator, patient in enumerate(patients.all()):
        logger.info("running {}/{}".format(iterator+1, total))
        load_patient(patient, async=False)


def any_loads_running():
    """
        returns a boolean as to whether any loads are
        running, for use by things that synch databases
    """
    patient_loading = models.InitialPatientLoad.objects.filter(
        state=models.InitialPatientLoad.RUNNING
    ).exists()

    batch_loading = models.BatchPatientLoad.objects.filter(
        state=models.BatchPatientLoad.RUNNING
    ).exists()

    return patient_loading or batch_loading


@timing
def load_demographics(hospital_number):
    started = timezone.now()
    try:
        result = api.demographics(hospital_number)
    except:
        stopped = timezone.now()
        logger.info("demographics load failed in {}".format(
            (stopped - started).seconds
        ))
        logger.error("Unable to run load_demographics{}".format(
            traceback.format_exc()
        ))
        return

    return result


def load_patient(patient, async=None):
    """
        Load all the things for a patient.

        This is called by the admin and by the add patient pathways
        Nuke all existing lab tests for a patient. Synch lab tests.

        will work asynchronously based on your preference.

        it will default to settings.ASYNC_API.
    """
    if async is None:
        async = settings.ASYNC_API

    models.InitialPatientLoad.objects.filter(
        state=models.InitialPatientLoad.RUNNING
    ).update(
        state=models.InitialPatientLoad.CANCELLED
    )

    patient_load = models.InitialPatientLoad(
        patient=patient,
    )
    patient_load.start()
    if async:
        async_task(patient, patient_load)
    else:
        _load_patient(patient, patient_load)


def async_task(patient, patient_load):
    from intrahospital_api import tasks
    tasks.load.delay(patient, patient_load)


def check_for_long_running_initial_patient_loads():
    an_hour_ago = timezone.now() - datetime.timedelta(hours=1)
    running_qs = models.InitialPatientLoad.objects.filter(
        state=models.InitialPatientLoad.RUNNING
    ).filter(
        started__lte=an_hour_ago
    )
    if running_qs.exists():
        logger.error(
            "We have long running initial patient loads"
        )


def good_to_go():
    """ Are we good to run a batch load, returns True if we should.
        runs a lot of sanity checks.
    """
    if not models.BatchPatientLoad.objects.all().exists():
        # an inital load is required via ./manage.py initial_test_load
        raise BatchLoadError(
            "We don't appear to have had an initial load run!"
        )

    current_running = models.BatchPatientLoad.objects.filter(
        Q(stopped=None) | Q(state=models.BatchPatientLoad.RUNNING)
    )

    if current_running.count() > 1:
        # we should never have multiple batches running at the same time
        raise BatchLoadError(
            "We appear to have {} concurrent batch loads".format(
                current_running.count()
            )
        )

    last_run_running = current_running.last()

    if last_run_running:
        time_ago = timezone.now() - last_run_running.started

        # If a batch load is still running and started less that
        # 10 mins ago, the let it run and don't try and run a batch load.
        #
        # Examples of when this might happen are when we've just done a
        # deployment.
        if time_ago.seconds < 600:
            logger.info(
                "batch still running after {} seconds, skipping".format(
                    time_ago.seconds
                )
            )
            return False
        else:
            if models.BatchPatientLoad.objects.all().count() == 1:
                # we expect the inital batch patient load to take ages
                # as its the first and runs the initial load
                # so cut it some slack
                logger.info(
                    "batch still running after {} seconds, but its the first \
load".format(time_ago.seconds)
                )
                return False
            else:
                raise BatchLoadError(
                    "Last load is still running and has been for {} mins".format(
                        time_ago.seconds/60
                    )
                )

    one_hour_ago = timezone.now() - datetime.timedelta(seconds=60 * 60)
    if models.BatchPatientLoad.objects.last().stopped < one_hour_ago:
        raise BatchLoadError("Last load has not run since {}".format(
            models.BatchPatientLoad.objects.last().stopped
        ))

    return True


def batch_load(force=False):
    all_set = None

    # validate that we can run without exception
    if not force:
        try:
            all_set = good_to_go()
        except:
            logger.error("Unable to run batch load \n{}".format(
                traceback.format_exc()
            ))

        if not all_set:
            return

    batch = models.BatchPatientLoad()
    batch.start()
    try:
        _batch_load(batch)
    except:
        batch.failed()
        logger.error("Unable to run batch load \n{}".format(
            traceback.format_exc()
        ))
    else:
        batch.complete()


def get_batch_start_time():
    """
        we need to paper over the cracks.

        usually this just means get me everything since the start
        of the last successful batch run.

        ie batch A starts at 10:00 and finishes at 10:03
        batch B will get all data since 10:00 so that nothing is lost

        however...
        the batches exclude initial patient loads, but usually that's ok
        but we have extra cracks to paper over...

        a patient load starts during the batch A load, at 9:58. It finishes
        the db load from the upstream db at 9:59 but is still saving the data
        to our db at 10:00

        it is excluded from the batch A, so batch B goes and starts its run
        from 9:59 accordingly.

    """
    last_successful_run = models.BatchPatientLoad.objects.filter(
        state=models.BatchPatientLoad.SUCCESS
    ).order_by("started").last()

    long_patient_load = models.InitialPatientLoad.objects.filter(
        state=models.InitialPatientLoad.SUCCESS
    ).filter(
        started__lt=last_successful_run.started
    ).filter(
        stopped__gt=last_successful_run.started
    ).order_by("started").first()

    if long_patient_load:
        return long_patient_load.started
    else:
        return last_successful_run.started


@timing
def _batch_load(batch):
    started = get_batch_start_time()

    # update the non reconciled
    update_demographics.reconcile_all_demographics()

    data_deltas = api.data_deltas(started)
    logger.info("loading in data delta")
    logger.info(json.dumps(data_deltas, indent=4))
    count = 0
    for data_delta in data_deltas:
        count += len(data_delta["lab_tests"])
    batch.count = count
    logger.info("loaded {} tests".format(count))
    update_from_batch(data_deltas)


@transaction.atomic
def update_patient_from_batch(demographics_set, data_delta):
    upstream_demographics = data_delta["demographics"]
    hospital_number = upstream_demographics["hospital_number"]
    nhs_number = upstream_demographics["nhs_number"]
    if hospital_number:
        patient_demographics_set = demographics_set.filter(
            hospital_number=hospital_number
        )
    elif nhs_number:
        patient_demographics_set = demographics_set.filter(
            nhs_number=nhs_number
        )
    else:
        logger.info("Unable to find an identifer for {}".format(
            data_delta
        ))
        return
    if not patient_demographics_set.exists():
        # this patient is not in our reconcile list,
        # move on, nothing to see here.
        logger.info("Unable to find a patient demographics set for {}".format(
            data_delta
        ))
        return

    patient = patient_demographics_set.first().patient
    update_demographics.update_patient_demographics(
        patient, upstream_demographics
    )
    update_lab_tests.update_tests(
        patient,
        data_delta["lab_tests"],
    )


@timing
def update_from_batch(data_deltas):
    # only look at patients that have been reconciled
    demographics_set = emodels.Demographics.objects.filter(
        external_system=EXTERNAL_SYSTEM
    )

    # ignore patients that have not had an existing patient load
    demographics_set = demographics_set.filter(
        patient__initialpatientload__state=models.InitialPatientLoad.SUCCESS
    )
    for data_delta in data_deltas:
        update_patient_from_batch(demographics_set, data_delta)


def async_load_patient(patient_id, patient_load_id):
    patient = Patient.objects.get(id=patient_id)
    patient_load = models.InitialPatientLoad.objects.get(
        id=patient_load_id
    )
    try:
        _load_patient(patient, patient_load)
    except:
        logger.error("Unable to run _load_patient \n{}".format(
            traceback.format_exc()
        ))
        raise


@transaction.atomic
def _load_patient(patient, patient_load):
    try:
        hospital_number = patient.demographics_set.first().hospital_number
        patient.labtest_set.filter(
            lab_test_type__in=[
                emodels.UpstreamBloodCulture.get_display_name(),
                emodels.UpstreamLabTest.get_display_name()
            ]
        ).delete()

        results = api.results_for_hospital_number(hospital_number)
        patient_load.count = len(results)
        update_lab_tests.update_tests(patient, results)
        demographics = api.demographics(
            patient.demographics_set.first().hospital_number
        )
        update_demographics.update_patient_demographics(patient, demographics)
    except:
        logger.info(traceback.format_exc())
        patient_load.failed()
        raise
    else:
        patient_load.complete()
