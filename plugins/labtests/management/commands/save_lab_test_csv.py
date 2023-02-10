from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from elcid import models as elcid_models
from elcid.utils import timing
from django.conf import settings
import pytds
import csv

SINCE = timezone.now() - datetime.timedelta(2)

# Get all results from upstream, order the results
# by the three fields that define a unique lab test
# so that in future when we iterate over to create
# observations we can cache the call to lab tests
GET_SOME_RESULTS = """
    SELECT * FROM tQuest.Pathology_Result_View
    WHERE date_inserted > @since
"""

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


def get_mrns_to_patient_id():
    mrn_to_patient_id = {}

    demo_mrn_and_patient_id = list(elcid_models.Demographics.objects.exclude(
            hospital_number=None,
        ).exclude(hospital_number="").values_list("hospital_number", "patient_id"))

    merged_mrn_and_patient_id = list(elcid_models.MergedMRN.objects.exclude(
            mrn=None,
        ).exclude(mrn="").values_list("mrn", "patient_id"))

    mrn_and_patient_id = demo_mrn_and_patient_id + merged_mrn_and_patient_id

    for i, v in mrn_and_patient_id:
        mrn_to_patient_id[i] = v
    return mrn_to_patient_id


@timing
def write_results():
    """
    Get all lab test data for MRNs that are within elcid.

    Strip the MRN of leading zeros before writing it to the file
    """
    hns = get_mrns_to_patient_id().keys()
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
                cur.execute(GET_SOME_RESULTS, params={"since": SINCE})
                while True:
                    rows = cur.fetchmany()
                    if not rows:
                        break
                    for row in rows:
                        key = get_key(row)
                        if not all(key):
                            continue
                        # lab tests sometimes have leading zeros
                        # we emulate the cerner master file and
                        # remove them.
                        if key[0].lstrip('0') not in hns:
                            continue
                        new_row = {k: v for k, v in row.items() if k in columns}
                        new_row["Patient_Number"] = new_row["Patient_Number"].lstrip('0')
                        writer.writerow(new_row)


def cast_to_lab_test_dict(row, patient_id):
    """
    Creates a dictionary from an upstream row with keys, values
    of what we want to save in our lab test model
    """
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


def cast_to_observation_dict(row, patient_id):
    """
    Creates a dictionary from an upstream row with keys, values
    of what we want to save in our observation model
    """
    result = {"patient_id": patient_id}
    result["lab_number"] = row["Result_ID"]
    result["test_name"] = row["OBR_exam_code_Text"]
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
    lab test.
    """
    return (
        row["Patient_Number"],
        row["Result_ID"],
        row["OBR_exam_code_Text"],
    )


def get_csv_fields(file_name):
    """
    Gets the column names from a csv file.
    """
    with open(file_name) as m:
        reader = csv.DictReader(m)
        headers = next(reader).keys()
    return list(headers)


@timing
def write_observation_csv():
    """
    Reads the results csv where the data exists as it exists
    in the upstream table.

    Writes the observation csv where the headers match our observation fields
    and the data is formatted into what we would save to our observation.
    It also adds the test_id column with the elcid lab test id in it.
    """
    hns = set()
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        for row in reader:
            hns = hns.union(row["Patient_Number"])
    hospital_number_to_patient_id = get_mrns_to_patient_id()
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        headers = cast_to_observation_dict(next(reader), 1).keys()
        m.seek(0)
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        with open(OBSERVATIONS_CSV, "w") as a:
            writer = None
            for idx, row in enumerate(reader):
                patient_id = hospital_number_to_patient_id[row["Patient_Number"]]
                obs_dict = cast_to_observation_dict(row, patient_id)
                if idx == 0:
                    writer = csv.DictWriter(a, fieldnames=headers)
                    writer.writeheader()
                writer.writerow(obs_dict)


@timing
def write_lab_test_csv():
    """
    Reads the results csv where the data exists as it exists
    in the upstream table.

    Writes the lab test csv where the headers match our lab test fields
    and the data is formatted into what we would save to our lab test.
    It also adds the patient_id column with the elcid patient id in it.
    """
    seen = set()
    hns = set()
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        for row in reader:
            hns = hns.union(row["Patient_Number"])
    hospital_number_to_patient_id = get_mrns_to_patient_id()
    writer = None
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        with open(LABTEST_CSV, "w") as a:
            for idx, row in enumerate(reader):
                key = get_key(row)
                if key in seen:
                    continue
                seen.add(key)
                patient_id = hospital_number_to_patient_id[row["Patient_Number"]]

                our_row = cast_to_lab_test_dict(row, patient_id)
                if idx == 0:
                    headers = our_row.keys()
                    writer = csv.DictWriter(a, fieldnames=headers)
                    writer.writeheader()
                writer.writerow(our_row)


class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        # Writes a csv of results as they exist in the upstream table
        write_results()

        # Writes a csv of lab tests with the fields they will have
        # in our table
        write_lab_test_csv()

        # Writes a csv of observations with the fields they will have
        # in our table
        write_observation_csv()
