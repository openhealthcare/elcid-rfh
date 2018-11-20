"""
Get a loader this.

This is the entry point to the api.

The api handles all interaction with the external system.

This handles our internals and relationship between elcid.

We have 4 entry points.

1. initial_load()

Administrator utility - can only be run from the Django shell.
Runs load_patient() for all patients.
Beware when running this, it has deletion side effects.

2. batch_load()

Load in tests for all patients if they exist in the lab test db
this is run every 5 mins and after deployments

Loads everything since the start of the previous
successful load so that we paper over any cracks.

3. load_patient()

Is what is run when we run it from the admin, or
after a patient has been reconciled from teh reconciliation pathway.
It loads in data for a single specific patient.

4. any_loads_running()
returns true if any, ie initial or batch, loads are running
"""
import traceback
from django.db import transaction
from django.conf import settings
from intrahospital_api import models
from opal.models import Patient
from elcid.utils import timing
from intrahospital_api.services.demographics import \
    service as demographics_service
from intrahospital_api.services.lab_tests import \
    service as lab_tests_service
from intrahospital_api.services.appointments import \
    service as appointments_service
from intrahospital_api.services.base import service_utils
from intrahospital_api import logger


@timing
def initial_load(remaining=False):
    """
    Runs an initial load.

    If you pass in remaining it will only run
    for patients that do not have an initialPatientLoad

    Otherwise it will clear out all inital loads and load
    in again
    """

    if not remaining:
        models.InitialPatientLoad.objects.all().delete()

    patients = Patient.objects.filter(initialpatientload=None)
    total = patients.count()

    for iterator, patient in enumerate(patients):
        logger.info("running {}/{}".format(iterator+1, total))
        load_patient(patient, run_async=False)


def log_errors(name):
    """
    Because we have lots of bare except: clauses we want to record those
    errors in the logs but carry on as if they didn't happen.
    """
    error = "unable to run {} \n {}".format(name, traceback.format_exc())
    logger.error(error)


def query_patient_demographics(hospital_number):
    """
    Public function to pass through a query by hospital number to the
    demographics service API
    """
    api = service_utils.get_api('demographics')
    demographics = None
    try:
        demographics = api.demographics_for_hospital_number(hospital_number)
    except:
        log_errors("query_patient_demographics")

    return demographics


def load_patient(patient, run_async=None):
    """
    Load all the things for a patient.

    This is called by the admin and by the add patient pathways.

    Nuke all existing lab tests for a patient.
    Synch lab tests.

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


def async_load_patient(patient_id, patient_load_id):
    patient = Patient.objects.get(id=patient_id)
    patient_load = models.InitialPatientLoad.objects.get(id=patient_load_id)
    try:
        _load_patient(patient, patient_load)
    except:
        log_errors("_load_patient")
        raise


@transaction.atomic
def _load_patient(patient, patient_load):
    logger.info(
        "started patient {} ipl {}".format(patient.id, patient_load.id)
    )
    try:
        demographics_service.load_patient(patient)
        lab_tests_service.refresh_patient(patient)
        appointments_service.refresh_patient(patient)
    except:
        patient_load.failed()
        raise
    else:
        patient_load.complete()
