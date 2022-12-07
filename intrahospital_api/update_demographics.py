"""
Handles updating demographics pulled in by the loader
"""
import datetime
import re
from plugins.monitoring.models import Fact
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
from elcid import constants, models

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


def has_master_file_timestamp_changed(
    patient, upstream_patient_information
):
    """
    Checks the inserted/last updated timestamp to see whether
    we need to update
    """
    master_file_metas = patient.masterfilemeta_set.all()

    if not master_file_metas:
        return True
    our_meta = master_file_metas[0]
    upstream_meta = upstream_patient_information[models.MasterFileMeta.get_api_name()]

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
    """
    Takes in an instance and dictionary of
    to update it with.

    Handle date/datetime conversion.

    Check to see if any of the fields have changed
    ignoring case.

    If a field has changed, update it and save the instance.
    """
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
            if new_val:
                if isinstance(field_type, DateTimeField):
                    new_val = deserialize_datetime(new_val)
                    if not timezone.is_aware(new_val):
                        new_val = timezone.make_aware(new_val)
                elif isinstance(field_type, DateField):
                    new_val = deserialize_date(new_val)

        # We get quite a few, title is Ms and title is MS changes
        # we don't care about tense so don't consider these
        # different.
        if isinstance(old_val, str) and isinstance(new_val, str):
            old_val_to_check = old_val.upper().strip()
            new_val_to_check = new_val.upper().strip()
            if not old_val_to_check == new_val_to_check:
                changed = True
        elif not old_val == new_val:
            changed = True

        if changed:
            setattr(instance, field, new_val)
    if changed:
        instance.updated_by = api.user
        instance.updated = timezone.now()
        instance.external_system = EXTERNAL_SYSTEM
        instance.save()


def get_mrn_and_date_from_merge_comment(merge_comment):
    """
    Takes in an merge comment e.g.
    " Merged with MRN 123456 Oct 18 2014 11:03AM  Merged with MRN 234567 on Oct 22 2013  4:44PM"
    returns a list of (MRN, datetime_merged,)
    """
    regex = r'Merged with MRN (?P<mrn>\w*\d*) on (?P<month>\w\w\w)\s(?P<day>[\s|\d]\d) (?P<year>\d\d\d\d)\s(?P<HHMM>[\s|\d]\d:\d\d)(?P<AMPM>[A|P]M)'
    found = list(set(re.findall(regex, merge_comment)))
    result = []
    for match in found:
        mrn = match[0]
        date_str = f"{match[2]} {match[1]} {match[3]} {match[4]}{match[5]}"
        merge_dt = datetime.datetime.strptime(date_str, "%d %b %Y %I:%M%p")
        result.append((mrn, timezone.make_aware(merge_dt),))
    # return by merged date
    return sorted(result, key=lambda x: x[1], reverse=True)


def get_related_rows_for_mrn(mrn):
    """
    Returns all merged MRNs related to the MRN including the row
    for the MRN from the CRS_Patient_Masterfile.

    The merged comments can be nested for for MRN x
    we can have MERGE_COMMENT "Merged with y on 21 Jan"
    Then for y we can have the merge comment "Merged with z on 30 Mar"
    This will return the rows for x, y and z

    If there are no related rows, ie the patient
    is not merged, return None.
    """
    query = """
    SELECT *
    FROM CRS_Patient_Masterfile
    WHERE Patient_Number = @mrn
    AND MERGED = 'Y'
    AND MERGE_COMMENTS <> ''
    AND MERGE_COMMENTS is not null
    """
    query_result = api.execute_hospital_query(
        query, {"mrn": mrn}
    )
    if not query_result:
        return None
    mrn_to_row = {mrn: query_result}
    related_mrns = [i[0] for i in get_mrn_and_date_from_merge_comment(query_result["MERGE_COMMENTS"])]
    for related_mrn in related_mrns:
        related_result = api.execute_hospital_query(
            query, {"mrn": related_mrn}
        )
        mrn_to_row[related_mrn] = related_result
        related_related_mrns = [
            i[0] for i in get_mrn_and_date_from_merge_comment(related_result["MERGE_COMMENTS"])
        ]
        for related_related_mrn in related_related_mrns:
            if related_related_mrn not in mrn_to_row:
                mrn_to_row[related_related_mrn] = api.execute_hospital_query(
                    query, {"mrn": related_related_mrn}
                )
    return list(mrn_to_row.values())



def update_patient_subrecords_from_upstream_dict(patient, upstream_patient_information):
    """
    Updates a patient's:
     * demographics,
     * gp details
     * contact details
     * next of kind details
    """
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
    # sometimes the CRS patient file includes hospital numbers
    # that have had leading 0s stripped.
    # we should never update the hospital_number, so restore it here
    hn = demographics.hospital_number
    upstream_demographics_dict["hospital_number"] = hn
    update_if_changed(demographics, upstream_demographics_dict)
    update_if_changed(gp_details, upstream_gp_details)
    update_if_changed(contact_information, upstream_contact_information)
    update_if_changed(next_of_kin_details, upstream_next_of_kin_details)


def update_patient_information(patient):
    """
    Updates a patient with the upstream demographics
    only their demographics they have changed.
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
    if not has_master_file_timestamp_changed(patient, upstream_patient_information):
        return

    update_patient_subrecords_from_upstream_dict(patient, upstream_patient_information)
    master_file_dict = upstream_patient_information[models.MasterFileMeta.get_api_name()]
    master_file_metas = patient.masterfilemeta_set.all()
    if master_file_metas:
        master_file_meta = master_file_metas[0]
    else:
        master_file_meta = models.MasterFileMeta(patient=patient)
    for key, value in master_file_dict.items():
        setattr(master_file_meta, key, value)
    master_file_meta.save()


def get_patients_from_master_file_rows(rows):
    """
    Returns all patients declared by the
    list of upstream dicts.

    This prefetches the things that we will then need.

    It also queries multiple times for small hns
    to handle the fact that on some occastion
    0 prefixes on hns are stripped off.
    """
    logger.info('starting patient query')
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
    logger.info('ending patient query')
    return hn_to_patients


def sync_recent_patient_information():
    """
    Syncs the patient information for
    the last four hours.
    """
    start = time()
    four_hours_ago = timezone.now() - datetime.timedelta(
        hours=4
    )
    changed_count = update_patient_information_since(
        four_hours_ago
    )
    end = time()
    Fact.objects.create(
        when=timezone.now(),
        label=constants.PATIENT_INFORMATION_SYNC_TIME,
        value_int=(end-start)
    )
    Fact.objects.create(
        when=timezone.now(),
        label=constants.PATIENT_INFORMATION_UPDATE_COUNT,
        value_int=changed_count
    )


@transaction.atomic
def update_patient_information_since(last_updated):
    """
    Updates all patient data that has changed since
    the datetime last_updated.

    Returns the number of patients updated
    """
    logger.info(
        f"patient information: loading patient information since {last_updated}"
    )
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
            if has_master_file_timestamp_changed(patient, row):
                update_patient_subrecords_from_upstream_dict(patient, row)
                master_file = models.MasterFileMeta(patient=patient)
                for k, v in row[models.MasterFileMeta.get_api_name()].items():
                    setattr(master_file, k, v)
                new_master_files.append(master_file)
    # By definition if the master file timestampo has changed the master file needs
    # to be updated. As this can happen thousands of times, the
    # fastest way is to delete the existing master file and bulk create
    models.MasterFileMeta.objects.filter(
        patient__in=[i.patient for i in new_master_files]
    ).delete()
    models.MasterFileMeta.objects.bulk_create(new_master_files)
    after_update = time()
    logger.info(f"patient information: query time {(after_query-before_query)/60}")
    logger.info(f"patient information: update time {(after_update-after_query)/60}")
    logger.info(f"patient information: row count {number_of_rows}")
    logger.info(f"patient information: patients found {number_of_patients_found}")
    logger.info(f"patient information: patients updated {len(new_master_files)}")
    return len(new_master_files)
