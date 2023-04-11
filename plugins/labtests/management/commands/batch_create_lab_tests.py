from intrahospital_api.apis.prod_api import PathologyRow, ProdApi as ProdAPI
from django.core.management.base import BaseCommand
from intrahospital_api import update_lab_tests
from elcid.models import Demographics
from collections import defaultdict
from django.utils import timezone
from elcid.utils import timing
import datetime

def run_query(query, params=None):
    """
    Returns a list of instances like
    {
        "demographics" : demographics, the first (ie the most recent) demographics result in the set.
        "lab_tests": all lab tests for the patient
    }
    """
    api = ProdAPI()
    if params:
        all_rows = api.execute_trust_query(query, params)
    else:
        all_rows = api.execute_trust_query(query)
    all_rows = [PathologyRow(r) for r in all_rows]
    hospital_number_to_rows = defaultdict(list)
    for row in all_rows:
        hospital_number_to_rows[row.get_hospital_number()].append(row)
    result = []
    for hospital_number, rows in hospital_number_to_rows.items():
        if Demographics.objects.filter(
            hospital_number=hospital_number
        ).exists():
            demographics = rows[0].get_demographics_dict()
            lab_tests = api.cast_rows_to_lab_test(rows)
            result.append(dict(
                demographics=demographics,
                lab_tests=lab_tests
            ))
    return result


def update_last_week():
    date_count = 7
    last_week = timezone.now() - datetime.timedelta(date_count)
    query = """
        SELECT * FROM tQuest.Pathology_Result_View
        WHERE date_inserted >= @start
        AND date_inserted < @end
    """
    for i in range((date_count + 1)):
        start = last_week + datetime.timedelta(i)
        end = last_week + datetime.timedelta(i + 1)
        print(f'start {start}')
        params = {"start": start, "end": end}
        result = run_query(query, params)
        update_from_queryset(result)


def update_from_queryset(data):
    demographics_set = Demographics.objects.all()
    for item in data:
        if not item['demographics']["hospital_number"]:
            continue
        patient_demographics_set = demographics_set.filter(
            hospital_number=item['demographics']["hospital_number"].lstrip('0')
        )
        if not patient_demographics_set.exists():
            continue  # Not in our cohort
        update_lab_tests.update_tests(patient_demographics_set.first().patient,  item["lab_tests"])


class Command(BaseCommand):
    @timing
    def handle(self, *a, **k):
        update_last_week()
