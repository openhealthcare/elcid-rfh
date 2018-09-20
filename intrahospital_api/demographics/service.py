"""
    Handles updating demographics pulled in by the api
"""
from django.db import transaction
from django.utils import timezone
from opal.models import Patient
from opal.core.serialization import deserialize_date
from intrahospital_api import logger
from intrahospital_api.base import service_utils
from intrahospital_api.constants import EXTERNAL_SYSTEM
from elcid.utils import timing


def update_external_demographics(
    patient,
    external_demographics_dict,
):
    """ Update the external demographics object so
        that it can be manually reconciled later.
    """
    external_demographics = patient.externaldemographics_set.get()
    external_demographics_dict.pop('external_system')
    external_demographics.update_from_dict(
        external_demographics_dict, service_utils.get_user(), force=True
    )


@timing
def sync_demographics():
    """ Iterate through all patients and sync their demographics
    """
    for patient in Patient.objects.all():
        sync_patient_demographics(patient)


@transaction.atomic
def sync_patient_demographics(patient):
    """ If a patient is from upstream, see if any details have change
        if so, update.

        If not but the patient has enough details to be seen as the same
        as a patient from upstream then synch with upstream.

        If not and the patient does not have enough details, then
        mark them for manual reconciliation
    """
    api = service_utils.get_api("demographics")
    demographics = patient.demographics_set.get()
    external_demographics_dict = api.demographics_for_hospital_number(
        demographics.hospital_number
    )
    if not external_demographics_dict:
        logger.info("unable to find {}".format(
            demographics.hospital_number
        ))
        return

    if demographics.external_system == EXTERNAL_SYSTEM:
        update_patient_demographics(patient, external_demographics_dict)
    elif is_reconcilable(patient, external_demographics_dict):
        update_patient_demographics(
            patient, external_demographics_dict
        )
    else:
        update_external_demographics(
            patient, external_demographics_dict
        )


def is_reconcilable(patient, external_demographics_dict):
    """ We need a patient to match on 
        first name, surname, dob and hospital number.

        If they do we can go ahead and update based on 
        what is on the upstream database.
    """
    # TODO, are we allowed to reconcile even if
    # the values are None?
    dob = external_demographics_dict["date_of_birth"]
    if dob:
        dob = deserialize_date(dob)
    return patient.demographics_set.filter(
        first_name__iexact=external_demographics_dict["first_name"],
        surname__iexact=external_demographics_dict["surname"],
        date_of_birth=dob,
        hospital_number=external_demographics_dict["hospital_number"]
    ).exists()


def have_demographics_changed(
    upstream_demographics, our_demographics_model
):
    """ Checks to see i the demographics have changed
        if they haven't, don't bother updating

        only compares keys that are coming from the
        upstream dict
    """
    as_dict = our_demographics_model.to_dict(service_utils.get_user())
    relevent_keys = set(upstream_demographics.keys())
    our_dict = {i: v for i, v in as_dict.items() if i in relevent_keys}
    return not upstream_demographics == our_dict


def update_patient_demographics(patient, upstream_demographics_dict=None):
    """ Updates a patient with the upstream demographics, if they have changed.
    """
    if upstream_demographics_dict is None:
        api = service_utils.get_api("demographics")
        upstream_demographics_dict = api.demographics_for_hospital_number(
            patient.demographics_set.first().hospital_number
        )
        # this should never really happen but has..
        # It happens in the case of a patient who has previously
        # matched with WinPath but who's hospital_number has
        # then been changed by the admin.
        if upstream_demographics_dict is None:
            return

    demographics = patient.demographics_set.get()
    if have_demographics_changed(
        upstream_demographics_dict, demographics
    ):
        demographics.update_from_dict(
            upstream_demographics_dict, service_utils.get_user(), force=True
        )


@timing
def for_hospital_number(hospital_number):
    started = timezone.now()
    api = service_utils.get_api("demographics")

    try:
        result = api.demographics_for_hospital_number(hospital_number)
    except:
        stopped = timezone.now()
        logger.error("demographics for hospital number failed in {}".format(
            (stopped - started).seconds
        ))
        return

    return result
    