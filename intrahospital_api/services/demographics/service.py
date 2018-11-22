"""
Demographics service for elCID RFH
"""
import datetime
from django.db import transaction
from django.utils import timezone
from opal.models import Patient
from opal.core.serialization import deserialize_date
from intrahospital_api import logger
from intrahospital_api.services.base import service_utils
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api.services.base import load_utils
from elcid.utils import timing


def update_external_demographics(
    patient,
    external_demographics_dict,
):
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY

    Update the external demographics object so
    that it can be manually reconciled later.
    """
    external_demographics = patient.externaldemographics_set.get()
    external_demographics_dict.pop('external_system')
    external_demographics.update_from_dict(
        external_demographics_dict, service_utils.get_user(), force=True
    )


def is_reconcilable(patient, external_demographics_dict):
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY

    We need a patient to match on
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


@timing
def load_patients():
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY

    Iterate through all patients and sync their demographics
    """
    changed = 0
    for patient in Patient.objects.all():
        synched = load_patient(patient)
        if synched:
            changed += 1
    return changed


def have_demographics_changed(
    upstream_demographics, our_demographics_model
):
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY

    Checks to see i the demographics have changed
    if they haven't, don't bother updating

    Only compares keys that are coming from the
    upstream dict
    """
    # upstream_demographics["date_of_birth"] = our_dict["date_of_birth"]
    as_dict = our_demographics_model.to_dict(service_utils.get_user())
    relevent_keys = set(upstream_demographics.keys())
    our_dict = {i: v for i, v in as_dict.items() if i in relevent_keys}
    to_compare = {}
    for k, v in upstream_demographics.items():
        if isinstance(our_dict[k], datetime.date):
            to_compare[k] = deserialize_date(v)
        else:
            to_compare[k] = v
    return not to_compare == our_dict


def update_patient_demographics(patient, upstream_demographics_dict=None):
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY

    Updates a patient with the upstream demographics, if they have changed.
    """
    if upstream_demographics_dict is None:
        backend = service_utils.get_backend("demographics")
        upstream_demographics_dict = backend.fetch_for_identifier(
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
        return True


@transaction.atomic
def load_patient(patient):
    """
    PUBLIC FUNCTION, CALLED EXTERNALLY

    If a patient is from upstream, see if any details have change if so,
    update.

    If not but the patient has enough details to be seen as the same as a
    patient from upstream then synch with upstream.

    If not and the patient does not have enough details, then mark them
    for manual reconciliation
    """
    api = service_utils.get_backend("demographics")
    demographics = patient.demographics_set.get()
    external_demographics_dict = api.fetch_for_identifier(
        demographics.hospital_number
    )
    if not external_demographics_dict:
        logger.info("unable to find {}".format(
            demographics.hospital_number
        ))
        return
    if demographics.external_system == EXTERNAL_SYSTEM:
        return update_patient_demographics(patient, external_demographics_dict)
    elif is_reconcilable(patient, external_demographics_dict):
        return update_patient_demographics(
            patient, external_demographics_dict
        )
    else:
        update_external_demographics(
            patient, external_demographics_dict
        )
        return


@timing
def for_hospital_number(hospital_number):
    """
    THIS FUNCTION NEVER CALLED INTERNALLY OR EXTERNALLY
    """
    started = timezone.now()
    api = service_utils.get_backend("demographics")

    try:
        result = api.fetch_for_identifier(hospital_number)
    except:
        stopped = timezone.now()
        logger.error("demographics for hospital number failed in {}".format(
            (stopped - started).seconds
        ))
        return

    return result


# not an invalid, name, its not a constant, seperate out
# for testing purposes
# pylint: disable=invalid-name
batch_load = load_utils.batch_load(
    service_name="demographics"
)(
    load_patients
)
