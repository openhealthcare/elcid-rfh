from django.core.management.base import BaseCommand
from elcid import models as elcid_models
from elcid import utils
from plugins.labtests import models as lab_models
from elcid.utils import timing
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from django.conf import settings
import subprocess
import pytds
import csv
import os


# Get all results from upstream, order the results
# by the three fields that define a unique lab test
# so that in future when we iterate over to create
# observations we can cache the call to lab tests
GET_ALL_RESULTS = """
    SELECT
    Patient_Number,
    Relevant_Clinical_Info,
    Observation_date,
    Request_Date,
    Result_ID,
    Specimen_Site,
    OBX_Status,
    Result_ID,
    OBR_exam_code_ID,
    OBR_exam_code_Text,
    Encounter_Consultant_Name,
    Encounter_Location_Code,
    Encounter_Location_Name,
    Accession_number,
    Department,
    last_updated,
    Observation_date,
    Reported_date,
    Result_Range,
    OBX_exam_code_Text,
    OBX_id,
    Result_Value,
    Result_Units
    FROM tQuest.Pathology_Result_View
"""

INSERT = """
BEGIN;
-- create a temp table tmp_lab_load which we will load in the csv
CREATE TEMP TABLE tmp_lab_load
ON COMMIT DROP
AS (
    SELECT {all_columns} FROM labtests_labtest, labtests_observation
    WHERE labtests_labtest.id = labtests_observation.test_id
    LIMIT 1000
)
WITH NO DATA;

-- create temporary indexes on columns that we are going to be querying
CREATE INDEX tmp_lab_load_index ON tmp_lab_load (patient_id, test_name, lab_number);
CREATE INDEX lab_index ON labtests_labtest (patient_id, test_name, lab_number);

-- copy in all the data into the csv this is all columns
-- except foreign keys, auto add and ids
COPY tmp_lab_load ({all_columns}) FROM '{csv_file}' DELIMITER ',' CSV HEADER;

-- if any rows that we have new version os
DELETE FROM labtests_labtest INNER JOIN tmp_lab_load
WHERE
    labtests_labtest.patient_id = tmp_lab_load.patient_id
    AND labtests_labtest.test_name = tmp_lab_load.test_name
    AND labtests_labtest.lab_number = tmp_lab_load.lab_number

-- why doesn't this cascade?
DELETE FROM labtests_observation
WHERE test_id NOT IN (
    select id from labtests_labtest
);

-- insert in our new data
INSERT INTO labtests_labtest ({lab_columns})
    SELECT distinct({lab_columns}) FROM tmp_lab_load
;

INSERT INTO labtests_observation (test_id,{obs_columns})
    SELECT labtests_labtest.id, {obs_columns_with_prefix} FROM
    tmp_lab_load, labtests_labtest
    WHERE
    tmp_lab_load.patient_id = labtests_labtest.patient_id
    AND tmp_lab_load.test_name = labtests_labtest.test_name
    AND tmp_lab_load.lab_number = labtests_labtest.lab_number
;

-- drop the index that we used
DROP INDEX lab_index;
END;
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


def get_mrn_to_patient_id():
    """
    Returns a map of all MRNs from demographics and Merged MRN
    to the corresponding patient id.
    """
    mrn_to_patient_id = {}
    demographics_mrn_and_patient_id = list(
        elcid_models.Demographics.objects.exclude(
            hospital_number=None,
        )
        .exclude(hospital_number="")
        .values_list("hospital_number", "patient_id")
    )

    for mrn, patient_id in demographics_mrn_and_patient_id:
        mrn_to_patient_id[mrn] = patient_id

    merged_mrn_and_patient_id = list(
        elcid_models.MergedMRN.objects.values_list("mrn", "patient_id")
    )

    for mrn, patient_id in merged_mrn_and_patient_id:
        mrn_to_patient_id[mrn] = patient_id

    return mrn_to_patient_id


@timing
def write_results():
    """
    Get all lab test data for MRNs that are within elcid.
    Create a row as we will save to our tables but without id, test id or
    our
    Lookup the patient id

    Strip the MRN of leading zeros before writing it to the file
    """
    mrn_to_patient_id = get_mrn_to_patient_id()
    with open(RESULTS_CSV, "w") as m:

        writer = None
        columns = set(COLUMNS)
        with pytds.connect(
            settings.TRUST_DB["ip_address"],
            settings.TRUST_DB["database"],
            settings.TRUST_DB["username"],
            settings.TRUST_DB["password"],
            as_dict=True,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(GET_ALL_RESULTS)
                while True:
                    rows = cur.fetchmany()
                    if not rows:
                        break
                    for upstream_row in rows:
                        if not upstream_row["Patient_Number"]:
                            continue
                        mrn = upstream_row["Patient_Number"].lstrip("0")
                        patient_id = mrn_to_patient_id.get(mrn)
                        if not patient_id:
                            continue
                        row = cast_to_lab_test_dict(upstream_row, patient_id)
                        row.update(cast_to_observation_dict(upstream_row))
                        if writer is None:
                            writer = csv.DictWriter(m, fieldnames=row.keys())
                            writer.writeheader()
                        writer.writerow({k: v for k, v in row.items() if k in columns})


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
    dep = row.get("Department")
    result["department_int"] = None
    if dep:
        result["department_int"] = int(dep)
    return result


def cast_to_observation_dict(row):
    """
    Creates a dictionary from an upstream row with keys, values
    of what we want to save in our observation model
    """
    result = {}
    result["last_updated"] = row["last_updated"]
    result["observation_datetime"] = row["Observation_date"]
    if not result["observation_datetime"]:
        result["observation_datetime"] = row["Request_Date"]
    result["reported_datetime"] = row["Reported_date"]
    result["reference_range"] = row["Result_Range"]
    result["observation_number"] = row["OBX_id"]
    result["observation_name"] = row["OBX_exam_code_Text"]
    result["observation_value"] = row["Result_Value"]
    result["units"] = row["Result_Units"]
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


def get_mrn_lab_number_test_name_to_test_id():
    values = lab_models.LabTest.objects.values_list(
        "patient__demographics__hospital_number", "lab_number", "test_name", "id"
    )
    result = {}
    for mrn, lab_number, test_name, test_id in values:
        result[
            (
                mrn,
                lab_number,
                test_name,
            )
        ] = test_id
    return result


@timing
def write_observation_csv():
    """
    Reads the results csv where the data exists as it exists
    in the upstream table.

    Writes the observation csv where the headers match our observation fields
    and the data is formatted into what we would save to our observation.
    It also adds the test_id column with the elcid lab test id in it.
    """
    mrn_lab_number_test_name_to_test_id = get_mrn_lab_number_test_name_to_test_id()
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        headers = cast_to_observation_dict(next(reader), 1).keys()
        m.seek(0)
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        with open(OBSERVATIONS_CSV, "w") as a:
            writer = None
            for idx, row in enumerate(reader):
                key = get_key(row)
                lt_id = mrn_lab_number_test_name_to_test_id[key]
                obs_dict = cast_to_observation_dict(row, lt_id)
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
            hns.add(row["Patient_Number"])
    hospital_number_to_patient_id = utils.find_patients_from_mrns(hns)
    writer = None
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        with open(LABTEST_CSV, "w") as a:
            for idx, row in enumerate(reader):
                key = get_key(row)
                if key in seen:
                    continue
                seen.add(key)
                patient_id = hospital_number_to_patient_id[row["Patient_Number"]].id

                our_row = cast_to_lab_test_dict(row, patient_id)
                if idx == 0:
                    headers = our_row.keys()
                    writer = csv.DictWriter(a, fieldnames=headers)
                    writer.writeheader()
                writer.writerow(our_row)


def call_db_command(sql):
    """
    Calls a command on our database via psql
    """
    subprocess.call(
        f"psql --echo-all -d {settings.DATABASES['default']['NAME']} -c \"{sql}\"",
        shell=True,
    )


def get_upstream_min_last_updated():
    """
    Returns the min last updated timestamp from the
    upstream lab test table.
    """
    api = ProdAPI()
    result = api.execute_trust_query(GET_MIN_LAST_UPDATED)
    return result[0][0]


def delete_lab_tests_and_observations_that_exist_upstream():
    """
    Delete all existing lab tests and observations that exist after the
    min(last_updated) of the upstream table.
    NOTE this cascades into infectious diseases and deletes
    all lab test relations in infectious diseases
    """
    last_updated = get_upstream_min_last_updated()
    call_db_command(COPY_OLD_LAB_TESTS_PSQL.format(last_updated))


def copy_lab_tests():
    """
    Runs the psql copy command to copy lab tests from
    LABTEST_CSV into our lab test table
    """
    columns = ",".join(get_csv_fields(LABTEST_CSV))
    pwd = os.getcwd()
    labtest_csv = os.path.join(pwd, LABTEST_CSV)
    cmd = f"\copy labtests_labtest ({columns}) FROM '{labtest_csv}' WITH (FORMAT csv, header);"
    call_db_command(cmd)


def copy_observations():
    """
    Runs the psql copy command to copy observations from
    OBSERVATIONS_CSV into our observation table
    """
    columns = ",".join(get_csv_fields(OBSERVATIONS_CSV))
    pwd = os.getcwd()
    observation_csv = os.path.join(pwd, OBSERVATIONS_CSV)
    cmd = f"\copy labtests_observation ({columns}) FROM '{observation_csv}' WITH (FORMAT csv, header);"
    call_db_command(cmd)


def check_db_command():
    """
    A sanity check to make sure we have permissions to
    run commands on our database.
    """
    call_db_command("SELECT count(*) FROM labtests_labtest")


def get_db_columns(model):
    all_fields = model._meta.get_fields()
    result = []
    fields_to_ignore = set(
        ["observation", "test", "created_at", "updated_at", "id", "infectionalert"]
    )
    for field in all_fields:
        field_name = field.name
        if field_name == "patient":
            field_name = "patient_id"
        if field_name not in fields_to_ignore:
            result.append(field_name)
    return result


class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        # check_db_command()

        # Writes a csv of results as they exist in the upstream table
        # write_results()
        pwd = os.getcwd()
        lab_columns = get_db_columns(lab_models.LabTest)
        obs_columns = get_db_columns(lab_models.Observation)
        command = INSERT.format(
            all_columns=",".join(lab_columns + obs_columns),
            lab_columns=",".join(lab_columns),
            obs_columns=",".join(obs_columns),
            obs_columns_with_prefix=",".join(
                [f"tmp_lab_load.{i}" for i in obs_columns]
            ),
            csv_file=os.path.join(pwd, RESULTS_CSV),
        )
        call_db_command(command)

        # Writes a csv of lab tests with the fields they will have
        # in our table
        # write_lab_test_csv()

        # # Deletes all existing lab tests and observations
        # # that have exist after the min(last_updated)
        # # in the upstream table.
        # # Note this will cascade and delete relations
        # delete_lab_tests_and_observations_that_exist_upstream()

        # # Copies the lab tests from the lab test csv into our
        # # table
        # copy_lab_tests()

        # # Writes a csv of observations with the fields they will have
        # # in our table
        # write_observation_csv()

        # # Copies the observations from the observation csv into our
        # # table
        # copy_observations()

        # lab_test_count = lab_models.LabTest.objects.all().count()
        # observation_count = lab_models.Observation.objects.all().count()
        # self.stdout.write(f"{lab_test_count} lab tests loaded")
        # self.stdout.write(f"{observation_count} observations loaded")
