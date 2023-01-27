from functools import lru_cache
from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from elcid import models as elcid_models
from plugins.labtests import models as lab_models
from elcid.utils import timing
from django.conf import settings
import subprocess
import pytds
import csv
import os

START_DATE = timezone.make_aware(datetime.datetime(2022, 1, 5, 14, 00))
END_DATE = timezone.make_aware(datetime.datetime(2022, 1, 5, 14, 30))

RESULTS_CSV = "results.csv"
LABTEST_CSV = "lab_tests.csv"
OBSERVATIONS_CSV = "observations.csv"

LAB_TEST_COLUMNS = [
    "Relevant_Clinical_Info",  # Becomes clinical info
    # Datetime ordered is observation date
    # if there is no observation date, we
    # use request date
    "Observation_date",
    "Request_Date",
    "Result_ID",  # Lab number
    "Specimen_Site",  # Site
    # Status, this comes through as
    # F for complete
    # There is also empty stryings, Nones
    # and 'I' that we store as Pending
    "OBX_Status",  # TODO is there more than one status per test number, test_ocde
    "Result_ID",  # lab number
    "OBR_exam_code_ID",  # test_code
    "OBR_exam_code_Text",  # test_name
    "Encounter_Consultant_Name",  # encounter_consultant_name
    "Encounter_Location_Code",  # encounter_location_code
    "Encounter_Location_Name",  # encounter_location_name
    "Accession_number",  # accession_number
    "Department",  # department_int
]

OBSERVATION_COLUMNS = [
    "last_updated",  # last_updated
    # observation_datetime is Observation_date
    # if this isn't populated its Request_Date
    "Observation_date",
    "Request_Date",
    "Reported_date",  # reported_datetime
    "Result_Range",  # reference_range
    "OBX_exam_code_Text",  # observation_name
    "OBX_id",  # observation_number
    "Result_Value",  # observation_value
    "Result_Units",  # units
]


COLUMNS = ["Patient_Number"] + LAB_TEST_COLUMNS + OBSERVATION_COLUMNS


@timing
def write_results():
    hns = set(
        elcid_models.Demographics.objects.exclude(
            hospital_number=None,
        )
        .exclude(hospital_number="")
        .values_list("hospital_number", flat=True)
    )
    query = """
    SELECT * FROM tQuest.Pathology_Result_View
    ORDER BY Patient_Number, Result_ID, OBR_exam_code_Text
    """
    params = {"since": START_DATE, "until": END_DATE}
    with open(RESULTS_CSV, "w") as m:
        writer = csv.DictWriter(m, fieldnames=COLUMNS)
        columns = set(COLUMNS)
        writer.writeheader()
        with pytds.connect(
            settings.TRUST_DB["ip_address"],
            settings.TRUST_DB["database"],
            settings.TRUST_DB["username"],
            settings.TRUST_DB["password"],
            as_dict=True,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                while True:
                    rows = cur.fetchmany()
                    if not rows:
                        break
                    for row in rows:
                        key = get_key(row)
                        if not all(key):
                            continue
                        if key[0] not in hns:
                            continue
                        writer.writerow({k: v for k, v in row.items() if k in columns})


def cast_to_lab_test_dict(row, patient_id):
    result = {"patient_id": patient_id}
    result["clinical_info"] = row["Relevant_Clinical_Info"]
    result["datetime_ordered"] = row.get("Observation_date")
    result["lab_number"] = row["Result_ID"]

    site = row["Specimen_Site"]
    if site and "^" in site and "-" in site:
        site = site.split("^")[1].strip().split("-")[0].strip()
    result["site"] = site

    status_abbr = row["OBX_Status"]

    if status_abbr == "F":
        status = "complete"
    else:
        status = "pending"
    result["status"] = status

    result["test_code"] = row["OBR_exam_code_ID"]
    result["test_name"] = row["OBR_exam_code_Text"]
    result["encounter_consultant_name"] = row["Encounter_Consultant_Name"]
    result["encounter_location_code"] = row["Encounter_Location_Code"]
    result["encounter_location_name"] = row["Encounter_Location_Name"]
    result["accession_number"] = row["Accession_number"]
    result["created_at"] = timezone.now()
    result["updated_at"] = timezone.now()
    dep = row.get("Department")
    result["department_int"] = None
    if dep:
        result["department_int"] = int(dep)
    return result


def cast_to_observation_dict(row, lab_test_id):
    result = {"test_id": lab_test_id}
    result["last_updated"] = row["last_updated"]
    result["observation_datetime"] = row["Observation_date"]
    if not result["observation_datetime"]:
        result["Request_Date"]
    result["reported_datetime"] = row["Reported_date"]
    result["reference_range"] = row["Result_Range"]
    result["observation_number"] = row["OBX_id"]
    result["observation_name"] = row["OBX_exam_code_Text"]
    result["observation_value"] = row["Result_Value"]
    result["units"] = row["Result_Units"]
    result["created_at"] = timezone.now()
    return result


def get_key(row):
    """
    Returns MRN, lab_number, test_name
    which are the three things that define a unique
    lab test
    """
    return (
        row["Patient_Number"],
        row["Result_ID"],
        row["OBR_exam_code_Text"],
    )


@lru_cache(maxsize=5096)
def get_lab_test_id(hospital_number, lab_number, test_name):
    return lab_models.LabTest.objects.get(
        patient__demographics__hospital_number=hospital_number,
        lab_number=lab_number,
        test_name=test_name,
    ).id


@timing
def write_observation_csv():
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        headers = cast_to_observation_dict(next(reader), 1).keys()
        m.seek(0)
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        with open(OBSERVATIONS_CSV, "w") as a:
            writer = csv.DictWriter(a, fieldnames=headers)
            writer.writeheader()
            for idx, row in enumerate(reader):
                if idx % 10000 == 0:
                    print(f'written {idx} rows to {OBSERVATIONS_CSV}')
                key = get_key(row)
                lt_id = get_lab_test_id(*key)
                obs_dict = cast_to_observation_dict(row, lt_id)
                writer.writerow(obs_dict)


def get_csv_fields(file_name):
    with open(file_name) as m:
        reader = csv.DictReader(m)
        headers = next(reader).keys()
        m.seek(0)
    return list(headers)


@timing
def write_lab_test_csv():
    seen = set()
    print("creating our our mrn to patient_id map")
    hns_and_patient_ids = elcid_models.Demographics.objects.all().values_list(
        "hospital_number", "patient_id"
    )
    hospital_number_to_patient_id = {i: v for i, v in hns_and_patient_ids}
    print("finished creating our our mrn to patient_id map")
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        headers = cast_to_lab_test_dict(next(reader), 1).keys()
        m.seek(0)
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        with open(LABTEST_CSV, "w") as a:
            writer = csv.DictWriter(a, fieldnames=headers)
            writer.writeheader()
            for idx, row in enumerate(reader):
                key = get_key(row)
                if key in seen:
                    continue
                seen.add(key)
                patient_id = hospital_number_to_patient_id[row["Patient_Number"]]
                our_row = cast_to_lab_test_dict(row, patient_id)
                if idx % 10000 == 0:
                    print(f'written {idx} row to {LABTEST_CSV}')
                writer.writerow(our_row)


def call_db_command(sql):
    subprocess.call(f"psql --echo-all -d {settings.DATABASES['default']['NAME']} -c '{sql}'", shell=True)


def delete_existing_lab_tests():
    call_db_command("truncate table labtests_labtest cascade;")


def delete_existing_observations():
    # TODO check this is necessary
    call_db_command("truncate table labtests_observation;")


def copy_lab_tests():
    columns = ",".join(get_csv_fields(LABTEST_CSV))
    pwd = os.getcwd()
    labtest_csv = os.path.join(pwd, LABTEST_CSV)
    cmd = f"\copy labtests_labtest ({columns}) FROM '{labtest_csv}' WITH (FORMAT csv, header);"
    call_db_command(cmd)


def copy_observations():
    columns = ",".join(get_csv_fields(OBSERVATIONS_CSV))
    pwd = os.getcwd()
    observation_csv = os.path.join(pwd, OBSERVATIONS_CSV)
    cmd = f"\copy labtests_observation ({columns}) FROM '{observation_csv}' WITH (FORMAT csv, header);"
    call_db_command(cmd)


def check_db_command():
    call_db_command("SELECT count(*) FROM labtests_labtest")


class Command(BaseCommand):
    def handle(self, *args, **options):
        # check_db_command()

        # write_results()
        # write_lab_test_csv()

        # delete_existing_lab_tests()

        # copy_lab_tests()
        delete_existing_observations()
        write_observation_csv()
        copy_observations()

        lab_test_count = lab_models.LabTest.objects.all().count()
        observation_count = lab_models.Observation.objects.all().count()
        print(f"{lab_test_count} lab tests loaded")
        print(f"{observation_count} observations loaded")
