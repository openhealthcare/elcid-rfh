"""
Load imaging data from upstream
"""
import time
from opal.core import serialization
from collections import defaultdict
from django.db import transaction
from elcid.models import Demographics, MergedMRN
from django.db.models import DateTimeField
from django.utils import timezone

from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from plugins.imaging.models import Imaging, PatientImagingStatus
from plugins.imaging import logger


Q_GET_IMAGING = """
SELECT *
FROM VIEW_ElCid_Radiology_Results
WHERE patient_number = @mrn
"""

Q_GET_IMAGING_SINCE = """
SELECT *
FROM VIEW_ElCid_Radiology_Results
WHERE
date_reported > @last_updated
"""


def load_imaging(patient):
    """
    Given a PATIENT, load any upstream imaging reports we do not have
    """
    api = ProdAPI()
    mrn = patient.demographics_set.all()[0].hospital_number
    merged_mrns = [i.mrn for i in patient.mergedmrns.all()]
    mrns = [mrn] + merged_mrns
    imaging_rows = []
    for mrn in mrns:
        imaging_rows.extend(api.execute_hospital_query(
            Q_GET_IMAGING, params={'mrn': mrn}
        ))
    created = update_imaging_from_query_result(imaging_rows)
    logger.info(
        f'Imaging patient load:Saved {len(created)} for Patient {patient.id}'
    )


def cast_to_instance(patient, imaging_dict):
    our_imaging = Imaging(patient=patient)
    for k, v in imaging_dict.items():
        if v:  # Ignore empty values
            fieldtype = type(
                Imaging._meta.get_field(Imaging.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k])
            )
            if fieldtype == DateTimeField:
                v = timezone.make_aware(v)
            setattr(
                our_imaging, Imaging.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v
            )
    return our_imaging


def get_changed_imaging_fields(old_instance, imaging_dict):
    changed = {}
    for their_label, our_field in old_instance.UPSTREAM_FIELDS_TO_MODEL_FIELDS.items():
        new_val = imaging_dict[their_label]
        old_val = getattr(old_instance, our_field)
        fieldtype = type(
            Imaging._meta.get_field(our_field)
        )
        if fieldtype == DateTimeField:
            new_val = timezone.make_aware(new_val)

        if not new_val == old_val:
            if new_val is None and old_val == "":
                continue
            if old_val is None and new_val == "":
                continue

            changed[our_field] = {
                "old_val": serialization._temporal_thing_to_string(old_val),
                "new_val": serialization._temporal_thing_to_string(new_val),
            }
    return changed


def load_imaging_since(last_updated):
    """
    Loads imaging from the upstream table that have
    been reported since last_updated.

    Returns the created imaging models
    """
    api = ProdAPI()
    query_start = time.time()
    imaging_rows = api.execute_hospital_query(
        Q_GET_IMAGING_SINCE,
        params={'last_updated': last_updated}
    )
    query_end = time.time()
    logger.info(f"Imaging: queries {len(imaging_rows)} rows in {query_end - query_start}s")
    created = update_imaging_from_query_result(imaging_rows)
    load_end = time.time()
    logger.info(f'Imaging: created {len(created)} in {load_end - query_end}')
    return created


@transaction.atomic
def update_imaging_from_query_result(imaging_rows):
    """
    Takes in the result from a db query.
    Ignores the rows where we don't need to update.
    Deletes old rows where we do need to update.

    Creates new rows, including rows with updates.

    Returns the created new rows.
    """
    existing_imaging = Imaging.objects.filter(
        sql_id__in=[i["SQL_Id"] for i in imaging_rows],
    )
    sql_id_to_existing_imaging = {
        ei.sql_id: ei for ei in existing_imaging
    }
    to_create = []
    to_delete = []
    hospital_numbers = {row["patient_number"].strip() for row in imaging_rows}
    demographics = Demographics.objects.filter(
        hospital_number__in=hospital_numbers
    ).select_related('patient')
    hospital_number_to_patients = defaultdict(list)
    for demo in demographics:
        hospital_number_to_patients[demo.hospital_number].append(
            demo.patient
        )

    merged_mrns = MergedMRN.objects.filter(
        mrn__in=hospital_numbers
    )
    for merged_mrn in merged_mrns:
        hospital_number_to_patients[merged_mrn.mrn].append(
            merged_mrn.patient
        )

    for row in imaging_rows:
        hn = row["patient_number"].strip()
        # if hn is empty, skip it
        if hn == "":
            continue
        if hn not in hospital_number_to_patients:
            continue

        for patient in hospital_number_to_patients[hn]:
            sql_id = row["SQL_Id"]

            # If its a new imaging record, add it to the to_create list
            if sql_id not in sql_id_to_existing_imaging:
                new_instance = cast_to_instance(patient, row)
                to_create.append(new_instance)
            else:
                existing_imaging = sql_id_to_existing_imaging[sql_id]
                # If its an existing image record and its newer then
                # our current image record, delete the existing
                # and create a new one, logging the difference between them.
                date_reported = timezone.make_aware(row["date_reported"])
                if date_reported > existing_imaging.date_reported:
                    patient_id = existing_imaging.patient_id
                    logger.debug(
                        f"Imaging: checking for patient id {patient_id} sql id {sql_id}"
                    )
                    changed = get_changed_imaging_fields(existing_imaging, row)
                    for k, v in changed.items():
                        logger.debug(
                            f'Imaging: updating {k} was {v["old_val"]} now {v["new_val"]}'
                        )
                    to_delete.append(existing_imaging)
                    new_instance = cast_to_instance(patient, row)
                    to_create.append(new_instance)

    Imaging.objects.filter(
        id__in=[i.id for i in to_delete]
    ).delete()
    Imaging.objects.bulk_create(to_create)
    PatientImagingStatus.objects.filter(
        patient_id__in=set([i.patient_id for i in to_create])
    ).update(
        has_imaging=True
    )
    return to_create
