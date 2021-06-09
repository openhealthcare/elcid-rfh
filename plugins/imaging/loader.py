"""
Load imaging data from upstream
"""
import datetime
from sys import hash_info
import time

from django.db import transaction
from elcid.models import Demographics
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

@transaction.atomic
def load_imaging(patient):
    """
    Given a PATIENT, load any upstream imaging reports we do not have
    """
    api = ProdAPI()

    demographic = patient.demographics()

    imaging_count = patient.imaging.count()

    existing_sql_ids = patient.imaging_set.values_list('sql_id', flat=True)

    imaging = api.execute_hospital_query(
        Q_GET_IMAGING,
        params={'mrn': demographic.hospital_number}
    )
    to_save = []
    for report in imaging:
        if imaging["SQL_ID"] in existing_sql_ids:
            continue
        our_imaging = cast_to_instance(patient, report)
        to_save.append(our_imaging)
    Imaging.objects.bulk_create(to_save)
    logger.info(f'Saved {len(to_save)} for Patient {patient.id}')

    if imaging_count == 0:
        if len(imaging) > 0:
            # This is the first time we've seen imaging results for this patient
            # Toggle their imaging flag
            PatientImagingStatus.objects.filter(patient=patient).update(
                has_imaging=True
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


@transaction.atomic
def load_imaging_since(last_updated):
    api = ProdAPI()
    query_start = time.time()
    imaging = api.execute_hospital_query(
        Q_GET_IMAGING_SINCE,
        params={'last_updated': last_updated}
    )
    query_end = time.time()
    logger.info(f"queries {len(imaging)} rows in {query_end - query_start}s")
    existing_imaging = set(Imaging.objects.filter(
        sql_id__in=[i["SQL_Id"] for i in imaging],
    ).values_list('sql_id', flat=True))
    logger.info(f'found existing {len(existing_imaging)}')
    without_existing = []
    for row in imaging:
        if row["SQL_Id"] not in existing_imaging:
            without_existing.append(row)
    by_hospital_number = {row["patient_number"]: row for row in imaging}
    demographics = Demographics.objects.filter(
        hospital_number__in=by_hospital_number.keys()
    ).select_related('patient')
    logger.info(f"the imaging refers to {len(demographics)} of our patients")
    new_imaging = []
    for demographic in demographics:
        # If they don't have a hospital number skip it.
        if not demographic.hospital_number:
            continue
        if demographic.hospital_number in by_hospital_number:
            row = by_hospital_number[demographic.hospital_number]
            new_imaging.append(cast_to_instance(demographic.patient, row))
    Imaging.objects.bulk_create(new_imaging)
    load_end = time.time()
    logger.info(f'created {len(new_imaging)} in {load_end - query_end}')
    PatientImagingStatus.objects.filter(
        patient_id__in=[i.patient_id for i in demographics]
    ).update(
        has_imaging=True
    )
