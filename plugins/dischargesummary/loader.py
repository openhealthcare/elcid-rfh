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

LOG_PREFIX = "Discharge Summary Loader:"

Q_GET_ALL_SUMMARIES_SINCE = """
SELECT * FROM VIEW_ElCid_Freenet_TTA_Main
WHERE CONVERT(DATETIME, LAST_UPDATED, 103) > @some_date
"""

Q_GET_ALL_MEDICATIONS_SINCE = """
SELECT * FROM VIEW_ElCid_Freenet_TTA_Drugs
WHERE TTA_Main_ID IN (
    SELECT SQL_Internal_ID FROM
    VIEW_ElCid_Freenet_TTA_Main
    WHERE CONVERT(DATETIME, LAST_UPDATED, 103) > @some_date
)
"""

Q_GET_SUMMARIES_FOR_MRN = """
SELECT *
FROM VIEW_ElCid_Freenet_TTA_Main
WHERE
RF1_NUMBER = @mrn
"""

Q_GET_MEDICATIONS_FOR_MRN = """
SELECT * FROM VIEW_ElCid_Freenet_TTA_Drugs
WHERE TTA_Main_ID IN (
    SELECT SQL_Internal_ID FROM
    VIEW_ElCid_Freenet_TTA_Main
    WHERE RF1_NUMBER = @mrn
)
"""
# If a patient is not in our database and they were discharged
# after 1/10/2021 then add them to the database
ADD_AFTER = datetime.datetime(2021, 10, 1)


def cast_to_datetime(some_str):
    """
    The last updated field is stored as a string and different formats are used
    """
    result = None
    formats = ['%d/%m/%Y %H:%M:%S', '%b %d %Y %I:%M%p', '%d/%m/%Y']
    for some_format in formats:
        try:
            result = datetime.datetime.strptime(some_str, some_format)
            break
        except ValueError:
            pass
    if result:
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
    hns = set([row['RF1_NUMBER'] for row in rows if row['RF1_NUMBER'].strip()])
    hn_to_patient_ids = defaultdict(list)
    demos = Demographics.objects.filter(hospital_number__in=hns)
    for demo in demos:
        hn_to_patient_ids[demo.hospital_number].append(
            demo.patient_id
        )
    discharge_summaries = []
    for row in rows:
        hn = row['RF1_NUMBER']
        if not hn.strip():
            continue
        if hn not in hns:
            significant_date = row["DATE_OF_DISCHARGE"] or row["DATE_OF_ADMISSION"]
            if significant_date and significant_date > ADD_AFTER:
                # If they are not in our system, we can just create them and let
                # the creation process create all of their discharge summaries
                create_rfh_patient_from_hospital_number(
                    hn, InfectionService
                )
                hns.add(hn)
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
        sql_id_to_discharge_summaries[discharge_summary.sql_internal_id].append(
            discharge_summary
        )

    discharge_medications = []
    for row in rows:
        for discharge_summary in sql_id_to_discharge_summaries.get(
            row["TTA_Main_ID"], []
        ):
            discharge_medication = cast_to_instance(DischargeMedication(), row)
            discharge_medication.discharge = discharge_summary
            discharge_medications.append(discharge_medication)
    DischargeMedication.objects.bulk_create(discharge_medications)


def delete_existing_summaries(rows):
    for row in rows:
        date_of_admission = None
        if row["DATE_OF_ADMISSION"]:
            date_of_admission = timezone.make_aware(row["DATE_OF_ADMISSION"])
        date_of_discharge = None
        if row["DATE_OF_DISCHARGE"]:
            date_of_discharge = timezone.make_aware(row["DATE_OF_DISCHARGE"])
        DischargeSummary.objects.filter(
            patient__demographics__hospital_number=row['RF1_NUMBER'],
            date_of_admission=date_of_admission,
            date_of_discharge=date_of_discharge,
        ).delete()


@transaction.atomic
def load_discharge_summaries_since(some_date):
    """
    Loads in and saves upstream discharge summaries/medications from an
    upstream result.

    Notably the last updated is stored as a string, and
    although we can convert it, that conversion requires
    a date not a datetime so we can only update based on date.

    We look at what's been updated and delete an discharge summaries
    with that mrn/date admitted/date discharged. We then create
    these with their attatched discharge medications.
    """
    logger.info(f'{LOG_PREFIX} started, summary loading since {some_date}')
    start_time = time.time()
    api = ProdAPI()
    summary_rows = api.execute_hospital_query(
        Q_GET_ALL_SUMMARIES_SINCE, params={"some_date": some_date}
    )
    end_summary_load_time = time.time()
    logger.info(
        f"{LOG_PREFIX} finished the summary load in {end_summary_load_time - start_time}"
    )
    logger.info(f'{LOG_PREFIX}, medication loading since {some_date}')
    api = ProdAPI()
    medication_rows = api.execute_hospital_query(
        Q_GET_ALL_MEDICATIONS_SINCE, params={"some_date": some_date}
    )
    end_medication_load_time = time.time()
    medication_load_duration = end_medication_load_time - end_summary_load_time
    logger.info(
        f"{LOG_PREFIX} finished the medication load in {medication_load_duration}"
    )
    logger.info(
        f"{LOG_PREFIX} starting the summary save"
    )
    delete_existing_summaries(summary_rows)
    save_discharge_summaries(summary_rows)
    summary_save_time = time.time()
    summary_save_duration = summary_save_time - end_medication_load_time
    logger.info(
        f"{LOG_PREFIX} finished the summary save in {summary_save_duration}"
    )
    save_medications(medication_rows)
    medication_save_time = summary_save_time = time.time()
    medication_save_duration = medication_save_time - summary_save_time
    logger.info(
        f"{LOG_PREFIX} finished the medication save in {medication_save_duration}"
    )
    logger.info(
        f"{LOG_PREFIX} finishing load discharge summaries since {some_date}"
    )


@transaction.atomic
def load_discharge_summaries(patient):
    api = ProdAPI()
    mrn = patient.demographics_set.all()[0].hospital_number
    logger.info(
        f"{LOG_PREFIX} starting to load discharge summaries for {mrn}"
    )
    DischargeSummary.objects.filter(
        patient__demographics__hospital_number=mrn
    ).delete()
    discharge_summary_rows = api.execute_hospital_query(
        Q_GET_SUMMARIES_FOR_MRN, params={"mrn": mrn}
    )
    save_discharge_summaries(discharge_summary_rows)
    discharge_medication_rows = api.execute_hospital_query(
        Q_GET_MEDICATIONS_FOR_MRN, params={"mrn": mrn}
    )
    save_medications(discharge_medication_rows)
    if len(discharge_summary_rows):
        PatientDischargeSummaryStatus.objects.filter(
            patient=patient
        ).update(
            has_dischargesummaries=True
        )
    else:
        PatientDischargeSummaryStatus.objects.filter(
            patient=patient
        ).update(
            has_dischargesummaries=False
        )
    logger.info(
        f"{LOG_PREFIX} finishing load discharge summaries for {mrn}"
    )
