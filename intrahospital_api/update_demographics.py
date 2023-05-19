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
from django.conf import settings
from opal.models import Patient
from opal.core.serialization import (
    deserialize_date, deserialize_datetime
)

from intrahospital_api import logger, loader, get_api, merge_patient
from intrahospital_api import merge_patient
from intrahospital_api.constants import EXTERNAL_SYSTEM
from elcid.utils import timing, send_email
from elcid import episode_categories as elcid_episode_categories
from elcid import constants, models

api = get_api()

GET_ALL_MERGED_MRNS_SINCE = """
    SELECT Patient_Number FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
    AND last_updated >= @since
"""

GET_MASTERFILE_DATA_FOR_MRN = """
    SELECT *
    FROM CRS_Patient_Masterfile
    WHERE Patient_Number = @mrn
"""

GET_MERGED_DATA_FOR_ALL_MERGED_PATIENTS = """
    SELECT Patient_Number, ACTIVE_INACTIVE, MERGE_COMMENTS, MERGED
    FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
"""

# If we receive more than this number, send an email
# notifiying the admins
MERGED_MRN_COUNT_EMAIL_THRESHOLD = 300


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


def get_all_merged_mrns_since(since):
    query_result = api.execute_hospital_query(
        GET_ALL_MERGED_MRNS_SINCE, params={"since": since}
    )
    return [i["Patient_Number"] for i in query_result]


class MergeException(Exception):
    pass


class CernerPatientNotFoundException(Exception):
    pass

def mrn_in_elcid(mrn):
    """
    Returns True if the MRN is in Demographics.hospital_number
    or MergedMRN.mrn fields
    """
    if models.MergedMRN.objects.filter(
        mrn=mrn
    ).exists():
        return True
    if models.Demographics.objects.filter(
        hospital_number=mrn
    ).exists():
        return True
    return False

def send_to_many_merged_mrn_email(cnt):
    """
    Sends an email saying we are creating more MergedMRNs than
    the MERGED_MRN_COUNT_EMAIL_THRESHOLD

    This is so we can take a look at the upstream data and
    check with upstream that the data is valid.
    """
    subject = f"We are creating {cnt} mergedMRNs"
    body = "\n".join([
        subject,
        "this is far more than we would expect and",
        f"breaches the threshold of {MERGED_MRN_COUNT_EMAIL_THRESHOLD}",
        f"please log in and check the upstream data"
    ])
    send_email(subject, body)

def get_or_create_active_patient(active_mrn):
    """
    Given an ACTIVE_MRN either return the patient,
    or _synchronously_ create that patient and return it.
    """
    active_patient = Patient.objects.filter(
        demographics__hospital_number=active_mrn
    ).first()

   if not active_patient:
        active_patient, _ = loader.get_or_create_patient(
            active_mrn,
            elcid_episode_categories.InfectionService,
            run_async=False
        )
    return active_patient   
    
def check_and_handle_upstream_merges_for_mrns(mrns):
    """
    Takes in a list of MRNs.

    Filters those not related to elCID.

    If they are inactive, creates a Patient for the
    active MRN and creates MergedMRN for all related inactive
    MRNs.

    If they are active, creates MergedMRN for all
    related inactive MRNs.
    """
    mrn_to_upstream_merge_data = get_mrn_to_upstream_merge_data()
    mrns_seen = set()
    active_patients_merged = set() # We won't want to reload them later    
    merged_mrns_to_create = []
    
    for mrn in mrns:
        active_mrn, merged_dicts = get_active_mrn_and_merged_mrn_data(
            mrn, mrn_to_upstream_merge_data
        )
        if active_mrn in mrns_seen:
        # The list passed into this function potentially contains all nodes in a merge graph            
            continue
        mrns_seen.add(active_mrn)
        
        if not mrn_in_elcid(active):
            if not any(mrn_in_elcid(i['mrn']) for i in merged_data):
                continue # no node in this graph is part of the elCID cohort        
                
        active_patient = get_or_create_active_patient(active_mrn)

        # Do we have to perform any merges our side? 
        merged_mrns = [i["mrn"] for i in merged_dicts]
        unmerged_patients = Patient.objects.filter(
            demographics__hospital_number__in=merged_mrns
        )
        for unmerged_patient in unmerged_patients:
            merge_patient.merge_patient(
                old_patient=unmerged_patient,
                new_patient=active_patient
            )
            patients_now_merged.add(active_patient)
                
        # Our copy of the merge graph
        for merged_dict in merged_dicts:
            if not MergedMRN.objects.filter(mrn=merged_dict['mrn']).exists():
                merged_mrns_to_create.append(
                    models.MergedMRN(
                        patient=active_patient,
                        our_merge_datetime=timezone.now(),
                        **merged_dict
                    )
                )
                
    if(len(merged_mrns_to_create)) > MERGED_MRN_COUNT_EMAIL_THRESHOLD:
        send_to_many_merged_mrn_email(len(merged_mrns_to_create))
        
    models.MergedMRN.objects.bulk_create(merged_mrns_to_create)
    logger.info(f'Saved {len(merged_mrns_to_create)} merged MRNs')

    # Patients who have had merge_patient called on them have
    # already been reloaded.
    # Other patients who have new merged MRNs need to be reloaded
    # to add in upstream data from the new merged MRN.
    patients_to_reload = set(i.patient for i in merged_mrns_to_create if i.patient not in active_patients_merged)
    for patient in list(patients_to_reload):
        loader.load_patient(patient)

def get_masterfile_row(mrn):
    """
    Takes in an MRN and returns the row from the master file.

    If there a multiple rows raise a ValueError as this
    should never be the case.
    """
    rows = api.execute_hospital_query(
        GET_MASTERFILE_DATA_FOR_MRN, {"mrn": mrn}
    )
    if len(rows) > 1:
        raise ValueError(f'Multiple results found for MRN {mrn}')
    if rows:
        return rows[0]

def parse_merge_comments(initial_mrn, mrn_to_upstream_merge_data):
    """
    Given a MRN, return an active related MRN (may be the same one),
    and a list of dictionaries of inactive mrns to be converted to
    MergedMRN instances

    Raise a MergeException if there are multiple active MRNs

    mrn_to_upstream_merge_data is a dictionary of MRN to
    "Patient_Number", "ACTIVE_INACTIVE", "MERGE_COMMENTS", "MERGED"
    fields of merged rows in the upstream database.

    This will be used first to get the upstream row rather than querying
    the upstream database each time.
    """
    parsed = set()
    related_mrns = [initial_mrn]
    active_mrn = None
    inactive_mrn_dicts = []
    if mrn_to_upstream_merge_data is None:
        mrn_to_upstream_merge_data = {}

    while len(related_mrns) > 0:
        next_mrn = related_mrns.pop(0)

        if next_mrn in parsed:
            continue
        else:
            parsed.add(next_mrn)

            next_row = mrn_to_upstream_merge_data.get(next_mrn)
            if not next_row:
                next_row = get_masterfile_row(next_mrn)
            if not next_row:
                raise MergeException(
                    f'Unable to find row for {next_mrn}'
                )

            merge_comments = next_row["MERGE_COMMENTS"]

            if not merge_comments:
                raise MergeException(
                    f'Unable to find merge comments for {next_mrn}'
                )

            if next_row["ACTIVE_INACTIVE"] == "ACTIVE":
                if active_mrn is None:
                    active_mrn = next_mrn
                else:
                    raise MergeException(
                        f'Multiple active related MRNs ({active_mrn}, {next_mrn}) found for {initial_mrn}'
                    )
            else:
                inactive_mrn_dicts.append({'mrn': next_mrn, 'merge_comments': merge_comments })

            merged_mrns = get_mrn_and_date_from_merge_comment(merge_comments)
            for found_mrn, _ in merged_mrns:
                if found_mrn in parsed:
                    continue
                else:
                    related_mrns.append(found_mrn)

    return active_mrn, inactive_mrn_dicts


def get_active_mrn_and_merged_mrn_data(mrn, mrn_to_upstream_merge_data=None):
    """
    For an MRN return the active MRN related to it (which could be itself)
    and a list of inactive MRNs that are associated with it.

    If there are no inactive MRNs or we are to say which is the
    active MRN return the MRN passed in and an empty list.

    Returns all merged MRNs related to the MRN including the row
    for the MRN from the CRS_Patient_Masterfile.


    The optional mrn_to_upstream_merge_data is a dictionary of MRN to
    "Patient_Number", "ACTIVE_INACTIVE", "MERGE_COMMENTS", "MERGED"
    fields of the upstream database. This will be used first to get
    the upstream row rather than querying the upstream database
    each time.

    The merged comments can be nested for for MRN x
    we can have MERGE_COMMENTS "Merged with y on 21 Jan"
    Then for y we can have the merge comment "Merged with z on 30 Mar"
    This will return the rows for x, y and z

    If the MRN is not marked as merged, return the MRN and an empty list
    If we are unable to process the merge comment, log an error
    return the MRN and an empty list.

    If we are unable to find the MRN in the master file return
    a CernerPatientNotFoundException. This should not happen.

    If the masterfile has multiple rows for an MRN a value
    error is raised by `get_masterfile_row` this
    suggests is something that we expect should never happen
    in the upstream system.
    """

    # mrn_to_upstream_merge_data is an optional dictionary of
    # mrn to upstream rows.
    if mrn_to_upstream_merge_data is None:
        mrn_to_upstream_merge_data = {}

    row = mrn_to_upstream_merge_data.get(mrn)
    if not row:
        row = get_masterfile_row(mrn)

    if row is None:
        raise CernerPatientNotFoundException(
            f'Unable to find a masterfile row for {mrn}'
        )
    if not row["MERGED"] == 'Y':
        # The patient is not merged
        return mrn, []
    if not row["MERGE_COMMENTS"]:
        logger.warn(
            f"MRN {mrn} is marked as merged but there is not merge comment"
        )
        return mrn, []

    try:
        active_mrn, merged_mrn_dicts = parse_merge_comments(mrn, mrn_to_upstream_merge_data)
    except MergeException as err:
        logger.warn(f"Merge exception raised for {mrn} with '{err}'")
        return mrn, []

    if not active_mrn:
        logger.warn(f"Unable to find an active MRN for {mrn}")
        return mrn, []

    return active_mrn, merged_mrn_dicts

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

def get_mrn_to_upstream_merge_data():
    """
    Returns a dictionary of {
        MRN: {
            Patient_Number,
            ACTIVE_INACTIVE,
            MERGE_COMMENTS,
            MERGED
        }
    }
    """
    result = api.execute_hospital_query(GET_MERGED_DATA_FOR_ALL_MERGED_PATIENTS)
    return {i["Patient_Number"]: i for i in result}


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
