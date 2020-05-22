"""
Functions for loading data from upstream.
"""
import datetime
import traceback
import json

from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from intrahospital_api import models
from opal.models import Patient

from elcid import models as emodels
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
        log_errors("initial_load")
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
        load_patient(patient, run_async=False)


def log_errors(name):
    error = "unable to run {} \n {}".format(name, traceback.format_exc())
    logger.error(error)


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
    result = patient_loading or batch_loading
    logger.info("Checking loads are running {}".format(result))
    return result


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
        log_errors("load_demographics")
        return

    return result


def create_rfh_patient_from_hospital_number(hospital_number, episode_category):
    """
    Creates a patient programatically and sets up integration.

    This is the recommended interface for new patients not via the UI.

    It will create a patient with HOSPITAL_NUMBER.
    It will create an episode of category EPISODE_CATEGORY for the patient.

    If a patient with this hospital number already exists raise ValueError
    """
    if emodels.Demographics.objects.filter(hospital_number=hospital_number).exists():
        raise ValueError('Patient with this hospital number already exists')

    patient = Patient.objects.create()

    demographics = patient.demographics()
    demographics.hospital_number = hospital_number
    demographics.save()

    patient.create_episode(
        category_name=episode_category.display_name,
        start=datetime.date.today()
    )

    load_patient(patient)


def load_patient(patient, run_async=None):
    """
    Load all the things for a patient.

    This is called by the admin and by the add patient pathways.

    Sync lab tests.
    Sync demographics.

    Will work asynchronously based on your preference.
    It will default to settings.ASYNC_API.
    """
    logger.info("starting to load patient {}".format(patient.id))
    if run_async is None:
        run_async = settings.ASYNC_API

    patient_load = models.InitialPatientLoad(
        patient=patient,
    )
    patient_load.start()
    if run_async:
        logger.info("loading patient {} asynchronously".format(patient.id))
        async_task(patient, patient_load)
    else:
        logger.info("loading patient {} synchronously".format(patient.id))
        _load_patient(patient, patient_load)


def async_task(patient, patient_load):
    from intrahospital_api import tasks
    # wait for all transactions to complete then launch the celery task
    # http://celery.readthedocs.io/en/latest/userguide/tasks.html#database-transactions
    transaction.on_commit(
        lambda: tasks.load.delay(patient.id, patient_load.id)
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

    three_hours_ago = timezone.now() - datetime.timedelta(seconds=60 * 180)
    if models.BatchPatientLoad.objects.last().stopped < three_hours_ago:
        raise BatchLoadError("Last load has not run since {}".format(
            models.BatchPatientLoad.objects.last().stopped
        ))

    return True


def batch_load(force=False):
    logger.info("starting batch load")
    all_set = None

    # validate that we can run without exception
    if not force:
        try:
            all_set = good_to_go()
        except:
            log_errors("batch load")

        if not all_set:
            return

    logger.info("good to go, commencing batch load")
    batch = models.BatchPatientLoad()
    batch.start()
    try:
        _batch_load()
    except:
        batch.failed()
        log_errors("batch load")
    else:
        batch.complete()


def get_batch_start_time():
    """
    Usually this just means get me everything since the start
    of the last successful batch run.

    Batch A starts at 10:00 and finishes at 10:03
    Batch B will get all data since 10:00

    The batches exclude initial patient loads, but usually that's ok

    however...

    A patient load starts during the batch A load, at 9:58. It finishes
    the db load from the upstream db at 9:59 but is still saving the data
    to our db at 10:00

    It is excluded from the batch A, so batch B goes and starts its run
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
def _batch_load():
    started = get_batch_start_time()

    logger.info("start loading batch")

    data_deltas = api.data_deltas(started)
    logger.info("calcualted data deltas")
    update_from_batch(data_deltas)


@transaction.atomic
def update_patient_from_batch(demographics_set, data_delta):
    upstream_demographics = data_delta["demographics"]
    patient_demographics_set = demographics_set.filter(
        hospital_number=upstream_demographics["hospital_number"]
    )
    if not patient_demographics_set.exists():
        # this patient is not in our reconcile list,
        # move on, nothing to see here.
        logger.info("unable to find a patient for {}".format(
            upstream_demographics["hospital_number"]
        ))
        return

    patient = patient_demographics_set.first().patient
    logger.info("updating patient demographics for {}".format(
        patient.id
    ))
    logger.info(json.dumps(upstream_demographics, indent=2))
    update_demographics.update_patient_demographics(
        patient, upstream_demographics
    )
    logger.info("updating patient results for {}".format(
        patient.id
    ))
    logger.info(json.dumps(data_delta["lab_tests"], indent=2))
    update_lab_tests.update_tests(
        patient,
        data_delta["lab_tests"],
    )
    logger.info("batch patient {} update complete".format(patient.id))


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
        logger.info("batch updating with {}".format(data_delta))
        update_patient_from_batch(demographics_set, data_delta)


def async_load_patient(patient_id, patient_load_id):
    patient = Patient.objects.get(id=patient_id)
    patient_load = models.InitialPatientLoad.objects.get(id=patient_load_id)
    try:
        _load_patient(patient, patient_load)
    except:
        log_errors("_load_patient")
        raise


def sync_all_patients():
    """
    A utility to go through all patients and
    sync them where possible.

    This is expected to be called from the shell
    """
    patients = Patient.objects.all().prefetch_related("demographics_set")
    count = patients.count()
    for number, patient in enumerate(patients):
        logger.info("Synching {} ({}/{})".format(
            patient.id, number+1, count
        ))
        try:
            sync_patient(patient)
        except Exception:
            log_errors("Unable to sync {}".format(patient.id))


def sync_patient(patient):
    hospital_number = patient.demographics_set.all()[0].hospital_number
    results = api.results_for_hospital_number(
        hospital_number
    )
    logger.info(
        "fetched results for patient {}".format(patient.id)
    )
    update_lab_tests.update_tests(patient, results)
    logger.info(
        "tests synced for {}".format(patient.id)
    )
    update_demographics.update_patient_demographics(patient)
    logger.info(
        "demographics synced for {}".format(patient.id)
    )


@transaction.atomic
def _load_patient(patient, patient_load):
    logger.info(
        "started patient {} ipl {}".format(patient.id, patient_load.id)
    )
    try:
        hospital_number = patient.demographics_set.first().hospital_number
        results = api.results_for_hospital_number(hospital_number)
        logger.info(
            "loaded results for patient {} {}".format(
                patient.id, patient_load.id
            )
        )
        logger.info(json.dumps(results, indent=2))
        update_lab_tests.update_tests(patient, results)
        logger.info(
            "tests updated for {} {}".format(patient.id, patient_load.id)
        )
        update_demographics.update_patient_demographics(patient)
        logger.info(
            "demographics updated for {} {}".format(
                patient.id, patient_load.id
            )
        )
    except:
        patient_load.failed()
        raise
    else:
        patient_load.complete()
