"""
Handles updating demographics pulled in by the loader
"""
import traceback

from django.db import transaction
from django.utils import timezone
from opal.models import Patient
from opal.core.serialization import deserialize_date

from intrahospital_api import logger
from intrahospital_api import get_api
from intrahospital_api.constants import EXTERNAL_SYSTEM
from elcid.utils import timing
from elcid import models

api = get_api()


def update_external_demographics(
    external_demographics,
    demographics_dict,
):
    external_demographics_fields = [
        "hospital_number",
        "nhs_number",
        "surname",
        "first_name",
        "title",
        "date_of_birth",
        "sex",
        "ethnicity",
        "death_indicator",
        "date_of_death"
    ]

    external_demographics_dict = {}
    for field in external_demographics_fields:
        result = demographics_dict.get(field)
        if result:
            external_demographics_dict[field] = result

    external_demographics.update_from_dict(
        external_demographics_dict, api.user, force=True
    )


@timing
def reconcile_all_demographics():
    """
        Look at all patients who have not been reconciled with the upstream
        demographics, ie there demographics external system is not
        EXTERNAL_SYSTEM.

        Take a look upstream, can we reconcile them by getting a match
        on a few different criteria.

        If not stick them on the reconcile list.
    """
    patients = Patient.objects.exclude(
        demographics__external_system=EXTERNAL_SYSTEM
    )

    for patient in patients:
        reconcile_patient_demographics(patient)


@transaction.atomic
def reconcile_patient_demographics(patient):
    """ for a patient,
    """
    demographics = patient.demographics_set.get()
    external_demographics_dict = api.demographics(
        demographics.hospital_number
    )
    if not external_demographics_dict:
        logger.info("unable to find {}".format(
            demographics.hospital_number
        ))
        return
    if is_reconcilable(patient, external_demographics_dict):
        demographics = patient.demographics_set.first()
        demographics.update_from_dict(
            external_demographics_dict, api.user, force=True
        )
    else:
        external_demographics = patient.externaldemographics_set.get()
        update_external_demographics(
            external_demographics, external_demographics_dict
        )


def is_reconcilable(patient, external_demographics_dict):
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


def has_information_changed(
    upstream_meta, our_meta
):
    """
    Checks the inserted/last updated timestamp to see whether
    we need to update
    """
    # this may not be necessary the fields may always be
    # populated, but lets be safe
    upstream_last_updated = upstream_meta["last_updated"]
    if not upstream_last_updated:
        upstream_last_updated = upstream_meta["insert_date"]

    upstream_last_updated = upstream_last_updated

    our_last_updated = our_meta.last_updated
    if not our_last_updated:
        our_last_updated = our_meta.insert_date

    if not our_last_updated:
        return True

    if upstream_last_updated > our_last_updated:
        return True
    return False


def update_patient_information(patient):
    """
    Updates a patient with the upstream demographics, if they have changed.
    """
    demographics = patient.demographics_set.all()[0]

    if not demographics.hospital_number:
        msg = " ".join([
            f"Patient {patient.id} has not hospital number",
            "skipping update information"
        ])
        logger.info(msg)
        return

    upstream_patient_information = api.patient_masterfile(
        demographics.hospital_number
    )

    # this should never really happen but has..
    # It happens in the case of a patient who has previously
    # matched with WinPath but who's hospital_number has
    # then been changed by the admin.
    if upstream_patient_information is None:
        logger.info(
            "No patient info found for {} skipping update information".format(
                patient.id
            )
        )
        return

    upstream_demographics_dict = upstream_patient_information[
        models.Demographics.get_api_name()
    ]

    upstream_gp_details = upstream_patient_information[
        models.GPDetails.get_api_name()
    ]
    gp_details = patient.gpdetails_set.all()[0]

    upstream_contact_information = upstream_patient_information[
        models.ContactInformation.get_api_name()
    ]
    contact_information = patient.contactinformation_set.all()[0]

    upstream_next_of_kin_details = upstream_patient_information[
        models.NextOfKinDetails.get_api_name()
    ]
    next_of_kin_details = patient.nextofkindetails_set.all()[0]

    upstream_master_file = upstream_patient_information[
        models.MasterFileMeta.get_api_name()
    ]
    master_file_meta, _ = models.MasterFileMeta.objects.get_or_create(
        patient=patient
    )

    if has_information_changed(
        upstream_patient_information[models.MasterFileMeta.get_api_name()],
        master_file_meta
    ):
        demographics.update_from_dict(
            upstream_demographics_dict, api.user, force=True
        )
        for field, value in upstream_gp_details.items():
            setattr(gp_details, field, value)
            gp_details.updated_by = api.user
            gp_details.save()

        for field, value in upstream_contact_information.items():
            setattr(contact_information, field, value)
            contact_information.updated_by = api.user
            contact_information.save()

        for field, value in upstream_next_of_kin_details.items():
            setattr(next_of_kin_details, field, value)
            next_of_kin_details.updated_by = api.user
            next_of_kin_details.save()

        for field, value in upstream_master_file.items():
            setattr(master_file_meta, field, value)
            master_file_meta.save()
        logger.info(
            "Patient info for {} is updated".format(
                patient.id
            )
        )
    else:
        logger.info(
            "Patient info for {} is unchanged".format(
                patient.id
            )
        )


def update_all_patient_information():
    """
    Runs update_patient_information for all_patients.

    Called by the management command sync_demographics which runs periodically
    """
    patient_qs = Patient.objects.all().prefetch_related('demographics_set')
    for patient in patient_qs:
        try:
            update_patient_information(patient)
        except Exception:
            msg = 'Exception syncing upstream demographics \n {}'
            logger.error(msg.format(traceback.format_exc()))
