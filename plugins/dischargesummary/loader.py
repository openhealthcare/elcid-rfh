"""
Load discharge summary data from upstream and save it
"""
from collections import defaultdict
import time
import datetime
from django.db import transaction
from django.db.models import DateTimeField
from elcid.episode_categories import InfectionService
from django.utils import timezone
from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from plugins.dischargesummary import logger
from plugins.dischargesummary.models import (
    DischargeSummary, DischargeMedication, PatientDischargeSummaryStatus
)

Q_GET_ALL_SUMMARIES = """
SELECT * FROM VIEW_ElCid_Freenet_TTA_Main
"""

Q_GET_ALL_MEDICATIONS = """
SELECT * FROM VIEW_ElCid_Freenet_TTA_Drugs
"""

# If a patient is not in our database and they were discharged
# after 1/10/2021 then add them to the database
ADD_AFTER = datetime.datetime(2021, 10, 1)


def cast_to_datetime(some_str):
    result = None
    try:
        result = datetime.datetime.strptime(some_str, '%d/%m/%Y %H:%M:%S')
    except ValueError:
        try:
            result = datetime.datetime.strptime(some_str, '%b %d %Y %I:%M%p')
        except ValueError:
            return
    return timezone.make_aware(result)


def cast_to_instance(instance, row):
    for k, v in row.items():
        if v:  # Ignore empty values
            fieldtype = type(
                instance.__class__._meta.get_field(
                    instance.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]
                )
            )
            if fieldtype == DateTimeField:
                v = timezone.make_aware(v)
            setattr(instance, instance.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v)
    instance.last_updated = cast_to_datetime(instance.last_updated_str)
    return instance


def save_discharge_summaries(rows):
    from intrahospital_api.loader import create_rfh_patient_from_hospital_number
    hns = [row['RF1_NUMBER'] for row in rows]
    hn_to_patient_ids = defaultdict(list)
    demos = Demographics.objects.filter(hospital_number__in=hns)
    for demo in demos:
        hn_to_patient_ids[demo.hospital_number].append(
            demo.patient_id
        )
    discharge_summaries = []
    for row in rows:
        hn = row['RF1_NUMBER']
        if hn not in hn_to_patient_ids:
            significant_date = row["DATE_OF_DISCHARGE"] or row["DATE_OF_ADMISSION"]
            if significant_date and significant_date > ADD_AFTER:
                discharge_summary = cast_to_instance(DischargeSummary(), row)
                discharge_summary.patient = create_rfh_patient_from_hospital_number(
                    hn, InfectionService
                )
                discharge_summaries.append(discharge_summary)
        else:
            for patient_id in hn_to_patient_ids[hn]:
                discharge_summary = cast_to_instance(DischargeSummary(), row)
                discharge_summary.patient_id = patient_id
                discharge_summaries.append(discharge_summary)
    DischargeSummary.objects.bulk_create(discharge_summaries)
    all_patient_ids = []
    for patient_ids in hn_to_patient_ids.values():
        all_patient_ids.extend(patient_ids)
    PatientDischargeSummaryStatus.objects.filter(
        patient_id__in=all_patient_ids
    ).update(
        has_dischargesummaries=True
    )


def save_medications(rows):
    discharge_summaries = DischargeSummary.objects.filter(
        sql_internal_id__in=[row['TTA_Main_ID'] for row in rows]
    )
    sql_id_to_discharge_summaries = defaultdict(list)
    for discharge_summary in discharge_summaries:
        sql_id_to_discharge_summaries[discharge_summary.sql_internal_id].append(discharge_summary)

    discharge_medications = []
    for row in rows:
        for discharge_summary in sql_id_to_discharge_summaries.get(
            row["TTA_Main_ID"], []
        ):
            discharge_medication = cast_to_instance(DischargeMedication(), row)
            discharge_medication.discharge = discharge_summary
            discharge_medications.append(discharge_medication)
    DischargeMedication.objects.bulk_create(discharge_medications)


@transaction.atomic
def load_all_discharge_summaries():
    logger.info("Loader started")
    start_time = time.time()
    api = ProdAPI()
    DischargeSummary.objects.all().delete()
    DischargeMedication.objects.all().delete()
    deleted_time = time.time()
    logger.info(
        f'Deleted discharge summaries/medications in {start_time - deleted_time}'
    )
    with api.hospital_query_batch_iterator(
        Q_GET_ALL_SUMMARIES, batch_size=1000
    ) as batch_loader:
        for rows in batch_loader:
            save_discharge_summaries(rows)
    discharge_summaries_loaded = time.time()
    logger.info(
        f'Created discharge summaries in {discharge_summaries_loaded - deleted_time}'
    )
    with api.hospital_query_batch_iterator(
        Q_GET_ALL_MEDICATIONS, batch_size=1000
    ) as batch_loader:
        for rows in batch_loader:
            save_medications(rows)
    discharge_medications_loaded = time.time()
    logger.info(
        f'Created discharge medications in {discharge_medications_loaded - discharge_summaries_loaded}'
    )
