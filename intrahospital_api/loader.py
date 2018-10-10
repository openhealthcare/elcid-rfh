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
load in tests for all patients if they exist in the lab test db
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
from intrahospital_api.exceptions import BatchLoadError
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api import update_demographics
from intrahospital_api.services.lab_tests import service as lab_tests
from intrahospital_api import logger
from intrahospital_api import get_api


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
    _initial_load()


def _initial_load():
    patients = Patient.objects.filter(initialpatientload=None)
    total = patients.count()

    for iterator, patient in enumerate(patients):
        logger.info("running {}/{}".format(iterator+1, total))
        load_patient(patient, run_async=False)


def log_errors(name):
    error = "unable to run {} \n {}".format(name, traceback.format_exc())
    logger.error(error)


def load_patient(patient, run_async=None):
    """
        Load all the things for a patient.

        This is called by the admin and by the add patient pathways
        Nuke all existing lab tests for a patient. Synch lab tests.

        will work asynchronously based on your preference.

        it will default to settings.ASYNC_API.
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


@timing
def load_demographics(hospital_number):
    started = timezone.now()
    api = get_api()
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


@transaction.atomic
def _load_patient(patient, patient_load):
    logger.info(
        "started patient {} ipl {}".format(patient.id, patient_load.id)
    )
    try:
        update_demographics.update_patient_demographics(patient)
        lab_tests.refresh_patient_lab_tests(patient)
    except:
        patient_load.failed()
        raise
    else:
        patient_load.complete()
