"""
Functions for loading data from upstream.
"""
import datetime
import traceback

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from opal.models import Patient

from elcid import models as emodels
from elcid.utils import timing
from plugins.admissions.loader import load_encounters, load_transfer_history_for_patient
from plugins.appointments.loader import load_appointments
from plugins.imaging.loader import load_imaging

from intrahospital_api import models
from intrahospital_api import get_api
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api import update_demographics
from intrahospital_api import update_lab_tests
from intrahospital_api import logger

api = get_api()


def log_errors(name):
    error = "unable to run {} \n {}".format(name, traceback.format_exc())
    logger.error(error)


@timing
def search_upstream_demographics(hospital_number):
    started = timezone.now()
    try:
        active_mrn, _ = update_demographics.get_active_mrn_and_merged_mrn_data(
            hospital_number
        )
        result = api.demographics(active_mrn)
    except:
        stopped = timezone.now()
        logger.info("searching upstream demographics failed in {}".format(
            (stopped - started).seconds
        ))
        log_errors("search_upstream_demographics")
        return

    return result


def create_rfh_patient_from_hospital_number(
    hospital_number, episode_category, run_async=None
):
    """
    Creates a patient programatically and sets up integration.

    This is the recommended interface for new patients not via the UI.

    It will create a patient with HOSPITAL_NUMBER.
    It will create an episode of category EPISODE_CATEGORY for the patient.

    If a patient with this hospital number already exists raise ValueError
    If a hospital number prefixed with zero is passed in raise ValueError
    If the hospital number has already been merged into another raise ValueError
    """
    if hospital_number.startswith('0'):
        raise ValueError(
            f'Unable to create a patient {hospital_number}. Hospital numbers within elCID should never start with a zero'
        )

    if emodels.Demographics.objects.filter(hospital_number=hospital_number).exists():
        raise ValueError('Patient with this hospital number already exists')

    if emodels.MergedMRN.objects.filter(mrn=hospital_number).exists():
        raise ValueError('MRN has already been merged into another MRN')

    active_mrn, merged_mrn_dicts = update_demographics.get_active_mrn_and_merged_mrn_data(
        hospital_number
    )

    patient = Patient.objects.create()
    patient.demographics_set.update(
        hospital_number=active_mrn
    )
    patient.episode_set.create(
        category_name=episode_category.display_name
    )

    for merged_mrn_dict in merged_mrn_dicts:
        patient.mergedmrn_set.create(**merged_mrn_dict)

    load_patient(patient, run_async=run_async)
    return patient


def load_patient(patient, run_async=None):
    """
    Load all the things for a patient.

    This is called by the admin and by the add patient pathways.

    Sync lab tests.
    Sync demographics.

    Will work asynchronously if RUN_ASYNC is python truthy
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


@timing
def _load_patient(patient, patient_load):
    logger.info(
        "Started patient {} Initial Load {}".format(patient.id, patient_load.id)
    )
    failed = []
    try:
        with transaction.atomic():
            hospital_number = patient.demographics_set.first().hospital_number
            results = api.results_for_hospital_number(hospital_number)
            logger.info(
                f"Loaded results for patient id {patient.id}"
            )
            update_lab_tests.update_tests(patient, results)
            logger.info(
                f"Tests updated for patient id {patient.id}"
            )
    except Exception:
        msg = f"Initial patient load for patient id {patient.id} failed on results"
        logger.error(f"{msg}\n{traceback.format_exc()}")
        failed.append('results')

    loaders = [
        update_demographics.update_patient_information,
        load_imaging,
        load_encounters,
        load_appointments,
        load_transfer_history_for_patient,
        # Discharge summaries are currently inaccurate
        # load_dischargesummaries
    ]

    for loader in loaders:
        loader_name = loader.__name__
        try:
            with transaction.atomic():
                loader(patient)
                logger.info(f'Completed {loader_name} for patient id {patient.id}')
        except Exception as ex:
            msg = f"Initial patient load for patient id {patient.id} failed on {loader_name}"
            logger.error(f"{msg}\n{traceback.format_exc()}")
            failed.append(loader_name)
    if failed:
        patient_load.failed()
    else:
        patient_load.complete()


def get_or_create_patient(
    mrn, episode_category, run_async=None
):
    """
    Get or create a opal.Patient with an opal.Episode of the
    episode category.

    If the patient is in the upstream Cerner master file, create the patient and
    load in the upstream data.

    If the patient is not found in the Cerner master file, create an elCID
    patient and do not attempt to query upstream data sources.

    If run_async is False the loaders that look for upstream data
    will be called synchronously.
    """
    patient = Patient.objects.filter(
        demographics__hospital_number=mrn
    ).first()
    if not patient:
        patient = Patient.objects.filter(
            mergedmrn__mrn=mrn
        ).first()

    if patient:
        patient.episode_set.get_or_create(
            category_name=episode_category.display_name
        )
        return (patient, False)
    try:
        patient = create_rfh_patient_from_hospital_number(
            mrn,
            episode_category,
            run_async=run_async
        )
    except update_demographics.CernerPatientNotFoundException:
        logger.info(
            f"Unable to find MRN {mrn} in Cerner, creating the patient without the upstream data"
        )
        patient = Patient.objects.create()
        patient.demographics_set.update(
            hospital_number=mrn
        )
        patient.episode_set.create(
            category_name=episode_category.display_name
        )
    return patient, True
