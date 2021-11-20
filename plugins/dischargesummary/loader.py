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


def delete_existing_medications(rows):
    DischargeMedication.objects.filter(
        tta_main_id__in=[row["TTA_Main_ID"] for row in rows]
    ).delete()


def load_discharge_summaries_since(some_date):
    """
    Loads discharge summaries from a certain date, deleting the existing
    and replacing them.
    """
    logger.info(f'{LOG_PREFIX} started, loading since {some_date}')
    start_time = time.time()
    api = ProdAPI()
    summary_rows = api.execute_hospital_query(
        Q_GET_ALL_SUMMARIES_SINCE, params={"some_date": some_date}
    )
    end_summary_load_time = time.time()
    logger.info(
        f"{LOG_PREFIX} finished the summary load in {end_summary_load_time - start_time}"
    )
    load_discharge_summaries_from_query_result(summary_rows)


@transaction.atomic
def load_discharge_summaries_from_query_result(summary_rows):
    """
    Saves upstream discharge summaries/medications from an
    upstream result.

    Notably the last updated is stored as a string, and
    although we can convert it, that conversion requires
    a date not a datetime so we can only update based on date.

    We look at what's been updated and delete an discharge summaries
    with that mrn/date admitted/date discharged. We then create
    these with their attatched discharge medications.
    """
    # Delete all the summaries, not this deletes the summaries
    # and any attached medications
    # Medications do not seem to be updated without the summary
    # also being updated
    # (not entirely true, there seem to be medications that
    # do not have a link to summary, we ignore these.)
    api = ProdAPI()
    delete_existing_summaries(summary_rows)
    deleted_time = time.time()
    logger.info(
        f"{LOG_PREFIX} deleted summaries in {deleted_time - end_summary_load_time}"
    )
    # Create our new summaries
    save_discharge_summaries(summary_rows)
    created_summary_time = time.time()
    logger.info(
        f"{LOG_PREFIX} created summaries in {created_summary_time - deleted_time}"
    )
    medication_rows = api.execute_hospital_query(
        Q_GET_ALL_MEDICATIONS_SINCE, params={"some_date": some_date}
    )
    save_medications(medication_rows)
    logger.info(
        f"{LOG_PREFIX} created medications in {time.time() - created_summary_time}"
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
    logger.info(
        f"{LOG_PREFIX} finishing load discharge summaries for {mrn}"
    )
