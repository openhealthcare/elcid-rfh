import gzip
import shutil
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from elcid import models as elcid_models
from plugins.labtests import models as lab_models
from elcid.utils import timing
from django.utils import timezone
from django.conf import settings
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
    WHERE Patient_Number IS NOT null
    AND Patient_Number <> ''
    AND Result_ID IS NOT null
    AND Result_ID <> ''
"""

DELETE = """
BEGIN;
-- create a temp table delete_or_keep which we will load patient number, lab number and test name
CREATE TEMP TABLE patient_id_lab_number_name (
    patient_id INT NOT NULL,
    lab_number VARCHAR (255) NOT NULL,
    test_name VARCHAR (255) NOT NULL
) ON COMMIT DROP;

COPY patient_id_lab_number_name (patient_id,lab_number,test_name) FROM '{csv_file}' DELIMITER ',' CSV HEADER;

CREATE INDEX lab_index ON labtests_labtest (patient_id, test_name, lab_number);

DELETE FROM ipc_infectionalert WHERE lab_test_id IN (
    SELECT labtests_labtest.id FROM labtests_labtest, patient_id_lab_number_name
    WHERE labtests_labtest.patient_id = patient_id_lab_number_name.patient_id
    AND labtests_labtest.test_name = patient_id_lab_number_name.test_name
    AND labtests_labtest.lab_number = patient_id_lab_number_name.lab_number
);

DELETE FROM labtests_labtest USING patient_id_lab_number_name
WHERE labtests_labtest.patient_id = patient_id_lab_number_name.patient_id
AND labtests_labtest.test_name = patient_id_lab_number_name.test_name
AND labtests_labtest.lab_number = patient_id_lab_number_name.lab_number;

DELETE FROM labtests_observation
WHERE NOT EXISTS (
    SELECT null
    FROM labtests_labtest
    WHERE labtests_observation.test_id = labtests_labtest.id
);
END;
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

-- copy in all the data into the csv this is all columns
-- except foreign keys, auto add and ids
COPY tmp_lab_load ({csv_columns}) FROM '{csv_file}' DELIMITER ',' CSV HEADER;

CREATE TEMP TABLE  old_lab_tests ON COMMIT DROP AS (
    SELECT * FROM labtests_labtest
    WHERE id NOT IN (
        select labtests_labtest.id
        FROM labtests_labtest, tmp_lab_load
        WHERE
        labtests_labtest.patient_id = tmp_lab_load.patient_id
        AND labtests_labtest.test_name = tmp_lab_load.test_name
        AND labtests_labtest.lab_number = tmp_lab_load.lab_number
    )
);

CREATE INDEX lab_index ON labtests_labtest (patient_id, test_name, lab_number);

-- insert in our new data
INSERT INTO labtests_labtest ({lab_columns})
    SELECT distinct {lab_columns} FROM tmp_lab_load
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
GZIPPED_RESULTS_CSV = "results.csv.gz"

PATIENT_ID_LAB_NUMBER_TEST_NAME_CSV = "patient_id_lab_number_test_name.csv"


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
                    to_delete = []
                    for upstream_row in rows:
                        if not upstream_row["Patient_Number"]:
                            continue
                        mrn = upstream_row["Patient_Number"].lstrip("0")
                        patient_id = mrn_to_patient_id.get(mrn)
                        if not patient_id:
                            continue
                        row = cast_to_lab_test_dict(upstream_row, patient_id)
                        row.update(cast_to_observation_dict(upstream_row))
                        to_delete.append(row)
                        if writer is None:
                            writer = csv.DictWriter(m, fieldnames=row.keys())
                            writer.writeheader()
                        writer.writerow({k: v for k, v in row.items()})


@timing
def write_lab_tests():
    rows = set()
    with open(RESULTS_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            patient_id = row["patient_id"]
            lab_number = row["lab_number"]
            test_name = row["test_name"]
            if (patient_id, lab_number, test_name,) in rows:
                continue
            else:
                rows.add((patient_id, lab_number, test_name,))

    with open(PATIENT_ID_LAB_NUMBER_TEST_NAME_CSV, 'w') as x:
        rows = list(rows)
        writer = csv.writer(x)
        writer.writerow(["patient_id", "lab_number", "test_name"])
        for row in rows:
            writer.writerow(row)

@timing
def delete_lab_test_file():
    os.remove(os.path.join(os.getcwd(), RESULTS_CSV))

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


def csv_columns():
    result = []
    with open(RESULTS_CSV) as f:
        reader = csv.reader(f)
        result = next(reader)
    return result

@timing
def gzip_file(file_name, gzipped_file_name):
    pwd = os.getcwd()
    with open(os.path.join(pwd, file_name), 'rb') as f_in:
        with gzip.open(os.path.join(pwd, gzipped_file_name), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(os.path.join(pwd, file_name))


@timing
def gunzip_file(file_name, gzipped_file_name):
    pwd = os.getcwd()
    with gzip.open(os.path.join(pwd, gzipped_file_name), 'rb') as f_in:
        with open(os.path.join(pwd, file_name), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(os.path.join(pwd, gzipped_file_name))


@timing
def run_delete_sql():
    pwd = os.getcwd()
    command = DELETE.format(csv_file=os.path.join(
        pwd, PATIENT_ID_LAB_NUMBER_TEST_NAME_CSV
    ))
    with connection.cursor() as cursor:
        cursor.execute(
            command
        )



class Command(BaseCommand):
    @timing
    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        print(f'starting {now}')
        # Writes a csv of results as they exist in the upstream table
        # write_results()

        pwd = os.getcwd()

        # write lab tests takes distinct patient id, lab number and test name
        # out of the results csv.
        # If we load the whole csv into a temp table and do the delete
        # and load in one go, then at some point we have...
        #  * all of the old data,
        #  * all of the new data in a temp table
        #  * all of the new on disk
        #
        # This takes more disk than we have.
        #
        # Solution is that we take the columns we need for the delete
        # gzip the results csv, do the delete of the old data and
        # then load
        # write_lab_tests()

        # gzip_file(RESULTS_CSV, GZIPPED_RESULTS_CSV)
        run_delete_sql()
        delete_lab_test_file()
        gunzip_file(RESULTS_CSV, GZIPPED_RESULTS_CSV)
        lab_columns = get_db_columns(lab_models.LabTest)
        obs_columns = get_db_columns(lab_models.Observation)
        command = INSERT.format(
            all_columns=",".join(lab_columns + obs_columns),
            csv_columns=",".join(csv_columns()),
            lab_columns=",".join(lab_columns),
            obs_columns=",".join(obs_columns),
            obs_columns_with_prefix=",".join(
                [f"tmp_lab_load.{i}" for i in obs_columns]
            ),
            csv_file=os.path.join(pwd, RESULTS_CSV),
        )
        with connection.cursor() as cursor:
            cursor.execute(
                command
            )
