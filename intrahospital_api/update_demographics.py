"""
Handles updating demographics pulled in by the loader
"""
import traceback
from time import time
from collections import defaultdict
from opal.core.fields import ForeignKeyOrFreeText
from django.db import transaction
from django.db.models import DateTimeField, DateField
from django.utils import timezone
from opal.models import Patient
from opal.core.serialization import (
    deserialize_date, deserialize_datetime
)

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

    our_last_updated = our_meta.last_updated
    if not our_last_updated:
        our_last_updated = our_meta.insert_date

    if not our_last_updated:
        return True

    if upstream_last_updated > our_last_updated:
        return True
    return False


def update_if_changed(instance, update_dict):
    time_start = time()
    changed = False
    for field, new_val in update_dict.items():
        old_val = getattr(instance, field)
        if old_val == new_val:
            continue
        if old_val == "" and new_val is None:
            continue
        if new_val == "" and old_val is None:
            continue

        cls = instance.__class__
        if not isinstance(getattr(cls, field), ForeignKeyOrFreeText):
            field_type = cls._meta.get_field(field)
            # note Datetime fields are inherited from DateField
            # so its important that this is this way around
            if isinstance(field_type, DateTimeField):
                new_val = deserialize_datetime(new_val)
                if new_val and not timezone.is_aware(new_val):
                    new_val = timezone.make_aware(new_val)
            elif isinstance(field_type, DateField):
                new_val = deserialize_date(new_val)
        if isinstance(old_val, str) and isinstance(new_val, str):
            if not old_val.upper() == new_val.upper():
                changed = True
        elif not old_val == new_val:
            changed = True

        if changed:
            logger.info(
                f"for {instance} {field} has changed was {old_val} now {new_val}"
            )
            setattr(instance, field, new_val)
    if changed:
        time_end = time()
        logger.info(f"updated {instance.__class__.__name__} in {time_end-time_start}")
        instance.updated_by = api.user
        instance.updated = timezone.now()
        instance.save()
        return True
    return False


def update_patient_from_upstream_dict(patient, upstream_patient_information):
    demographics = patient.demographics_set.all()[0]
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

    master_file_metas = patient.masterfilemeta_set.all()

    if master_file_metas:
        master_file_meta = master_file_metas[0]
    else:
        master_file_meta = models.MasterFileMeta(patient=patient)

    if has_information_changed(
        upstream_patient_information[models.MasterFileMeta.get_api_name()],
        master_file_meta
    ):
        # we should never update the hospital_number
        upstream_demographics_dict["hospital_number"] = demographics.hospital_number
        update_if_changed(demographics, upstream_demographics_dict)
        update_if_changed(gp_details, upstream_gp_details)
        update_if_changed(contact_information, upstream_contact_information)
        update_if_changed(next_of_kin_details, upstream_next_of_kin_details)
        logger.info(
            "Patient info for {} is updated".format(
                patient.id
            )
        )
        return True
    else:
        logger.info(
            "Patient info for {} is unchanged".format(
                patient.id
            )
        )
        return False


def update_patient_information(patient):
    """
    Updates a patient with the upstream demographics, if they have changed.
    """
    demographics = patient.demographics_set.all()[0]
    hospital_number = demographics.hospital_number

    if not hospital_number:
        msg = " ".join([
            f"Patient {patient.id} has not hospital number",
            "skipping update information"
        ])
        logger.info(msg)
        return

    upstream_patient_information = api.patient_masterfile(
        hospital_number
    )

    if upstream_patient_information is None:
        # If the hn begins with leading 0(s)
        # the data is sometimes empty in the CRS_* fields.
        # So if we cannot find rows with 0 prefixes
        # remove the prefix
        upstream_patient_information = api.patient_masterfile(
            hospital_number.lstrip("0")
        )
        # If we have stripped off the 0 make sure we don't
        # overwrite the demographics.hospital number
        upstream_demographics_dict = upstream_patient_information[
            models.Demographics.get_api_name()
        ]
        upstream_demographics_dict["hospital_number"] = hospital_number

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

    update_patient_from_upstream_dict(patient, upstream_patient_information)


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


def get_patients_from_master_file_rows(rows):
    print('starting patient query')
    hns = []
    for row in rows:
        hn = row["demographics"]["hospital_number"]
        if hn:
            hns.append(hn)

    patients = Patient.objects.filter(
        demographics__hospital_number__in=hns
    ).prefetch_related(
        'demographics_set',
        'gpdetails_set',
        'contactinformation_set',
        'nextofkindetails_set',
        'masterfilemeta_set'
    )
    hn_to_patients = defaultdict(list)
    for patient in patients:
        hn_to_patients[patient.demographics_set.all()[0].hospital_number].append(
            patient
        )

    for hn in hns:
        hn = row["demographics"]["hospital_number"]
        if len(hn) < 7:
            for i in range(1, 3):
                new_hn = hn.zfill(i)
                patients = Patient.objects.filter(
                    demographics__hospital_number=new_hn
                )
                hn_to_patients[hn].extend(list(patients))
    print('ending patient query')
    return hn_to_patients


@transaction.atomic
def update_patient_information_since(last_updated):
    new_master_files = []
    before_query = time()
    # db query
    rows = api.patient_masterfile_since(last_updated)
    after_query = time()
    number_of_rows = len(rows)
    number_of_patients_found = 0
    # update
    hn_to_patients = get_patients_from_master_file_rows(rows)
    for row in rows:
        hn = row[models.Demographics.get_api_name()]["hospital_number"]
        patients = hn_to_patients.get(hn, [])
        number_of_patients_found += 1
        for patient in patients:
            changed = update_patient_from_upstream_dict(patient, row)
            if changed:
                master_file = models.MasterFileMeta(patient=patient)
                for k, v in row[models.MasterFileMeta.get_api_name()].items():
                    setattr(master_file, k, v)
                new_master_files.append(master_file)
    # By definition if the information has changed the master file needs
    # to be updated, as this happens thousands of times, the
    # fastest way is to delete the existing master file and bulk create
    models.MasterFileMeta.objects.filter(
        patient__in=[i.patient for i in new_master_files]
    ).delete()
    models.MasterFileMeta.objects.bulk_create(new_master_files)
    after_update = time()
    print(f"query time {(after_query-before_query)/60}")
    print(f"update time {(after_update-after_query)/60}")
    print(f"row count {number_of_rows}")
    print(f"patients found {number_of_patients_found}")
    print(f"patients updated {len(new_master_files)}")
    raise ValueError('roll back the transaction')
