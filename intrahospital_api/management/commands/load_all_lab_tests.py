from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from intrahospital_api import logger
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

UPSTREAM_DB_COLUMNS = "Patient_Number," + ",".join(LAB_TEST_COLUMNS) + "," + ",".join(OBSERVATION_COLUMNS)

# Get all results from upstream, order the results
# by the three fields that define a unique lab test
# so that in future when we iterate over to create
# observations we can cache the call to lab tests
GET_ALL_RESULTS = f"""
    SELECT
    {UPSTREAM_DB_COLUMNS}
    FROM tQuest.Pathology_Result_View
    WHERE Patient_Number IS NOT null
    AND Patient_Number <> ''
    AND Result_ID IS NOT null
    AND Result_ID <> ''
"""

DELETE = """
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

DROP INDEX lab_index;
"""


RESULTS_CSV = "results.csv"
OBSERVATIONS_CSV = "observations.csv"
LABTEST_CSV = "lab_tests.csv"
DELETE_CSV = "patient_id_lab_number_test_name.csv"


@timing
def get_mrn_to_patient_id():
    """
    Returns a map of all MRNs from demographics and Merged MRN
    to the corresponding patient id.
    """
    mrn_to_patient_id = {}
    demographics_mrn_and_patient_id = elcid_models.Demographics.objects.exclude(
        hospital_number=None,
    ).exclude(hospital_number="").values_list("hospital_number", "patient_id")

    for mrn, patient_id in demographics_mrn_and_patient_id:
        mrn_to_patient_id[mrn] = patient_id

    merged_mrn_and_patient_id = elcid_models.MergedMRN.objects.values_list("mrn", "patient_id")

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
                    for upstream_row in rows:
                        if not upstream_row["Patient_Number"]:
                            continue
                        mrn = upstream_row["Patient_Number"].lstrip("0")
                        patient_id = mrn_to_patient_id.get(mrn)
                        if not patient_id:
                            continue
                        if upstream_row["Result_ID"] is None:
                            continue
                        if len(upstream_row["Result_ID"].strip()) == 0:
                            continue
                        if upstream_row["OBR_exam_code_Text"] is None:
                            continue
                        if len(upstream_row["OBR_exam_code_Text"].strip()) == 0:
                            continue
                        columns = ["patient_id"] + LAB_TEST_COLUMNS + OBSERVATION_COLUMNS
                        if writer is None:
                            writer = csv.DictWriter(m, fieldnames=columns)
                            writer.writeheader()
                        row = {"patient_id": patient_id}
                        for k, v in upstream_row.items():
                            if not k == 'Patient_Number':
                                row[k] = v
                        writer.writerow(row)

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
    writer = None
    with open(RESULTS_CSV) as m:
        reader = csv.DictReader(m)
        with open(LABTEST_CSV, "w") as a:
            for idx, row in enumerate(reader):
                key = (row["patient_id"], row["Result_ID"], row["OBR_exam_code_Text"],)
                if key in seen:
                    continue
                seen.add(key)
                our_row = cast_to_lab_test_dict(row)
                if idx == 0:
                    headers = our_row.keys()
                    writer = csv.DictWriter(a, fieldnames=headers)
                    writer.writeheader()
                writer.writerow(our_row)


def get_delete_ids():
    delete_ids = []
    for key_to_id in yield_patient_id_lab_number_test_name_to_test_id():
        with open(LABTEST_CSV) as l:
            reader = csv.DictReader(l)
            for row in reader:
                key = (int(row["patient_id"]), row["lab_number"], row["test_name"])
                lab_test_id = key_to_id.get(key)
                if lab_test_id:
                    delete_ids.append(lab_test_id)
        logger.info(f'found {len(delete_ids)}')
        yield delete_ids


@timing
def run_delete():
    cnt = 0
    for delete_ids_list in get_delete_ids():
        if not delete_ids_list:
            break
        cnt += len(delete_ids_list)
        delete_ids = ",".join([str(i) for i in delete_ids_list])
        logger.info(f'Running the delete for {len(delete_ids_list)}')

        query = f"""
            DELETE FROM ipc_infectionalert WHERE lab_test_id IN ({delete_ids})
        """
        call_db_command(query)
        query = f"""
            DELETE FROM labtests_labtest WHERE id IN ({delete_ids})
        """
        call_db_command(query)
        query = f"""
            DELETE FROM labtests_observation WHERE id IN ({delete_ids})
        """
        call_db_command(query)
        logger.info('Delete section complete')
    logger.info(f"Deleted {cnt}")
    send_email(f'Done deleting {cnt}')


def send_email(msg):
    send_mail(msg, msg, settings.DEFAULT_FROM_EMAIL, settings.ADMINS)

@timing
def write_observation_csv():
    """
    Reads the results csv where the data exists as it exists
    in the upstream table.

    Writes the observation csv where the headers match our observation fields
    and the data is formatted into what we would save to our observation.
    It also adds the test_id column with the elcid lab test id in it.
    """
    with open(OBSERVATIONS_CSV, "w") as a:
        for patient_id_lab_number_test_name_to_test_id in yield_patient_id_lab_number_test_name_to_test_id():
            with open(RESULTS_CSV) as m:
                reader = csv.DictReader(m)
                writer = None
                for row in reader:
                    key = (row["patient_id"], row["Result_ID"], row["OBR_exam_code_Text"],)
                    lt_id = patient_id_lab_number_test_name_to_test_id.get(key)
                    if not lt_id:
                        continue
                    obs_dict = cast_to_observation_dict(row, lt_id)
                    if writer is None:
                        writer = csv.DictWriter(a, fieldnames=obs_dict.keys())
                        writer.writeheader()
                    writer.writerow(obs_dict)


def yield_patient_id_lab_number_test_name_to_test_id(amt=300000):
    values = lab_models.LabTest.objects.values_list(
        'patient_id',
        'lab_number',
        'test_name',
        'id'
    ).order_by()
    result = {}
    for patient_id, lab_number, test_name, test_id in values:
        result[(patient_id, lab_number, test_name,)] = test_id
        if len(result) > amt:
            yield result
            result = {}
    yield result

def cast_to_lab_test_dict(row):
    """
    Creates a dictionary from an upstream row with keys, values
    of what we want to save in our lab test model
    """
    result = {"patient_id": row["patient_id"]}
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
    result["created_at"] = timezone.now()
    result["updated_at"] = timezone.now()
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
    result["created_at"] = timezone.now()
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


def call_db_command(sql):
    with connection.cursor() as cursor:
        cursor.execute(
            sql
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
def copy_lab_tests():
    cwd = os.getcwd()
    lab_columns = ",".join(get_csv_fields(LABTEST_CSV))
    lab_test_csv = os.path.join(cwd, LABTEST_CSV)
    copy_in_lab_tests = f"""
        COPY labtests_labtest({lab_columns}) FROM '{lab_test_csv}' WITH (FORMAT csv, header);
    """
    call_db_command(copy_in_lab_tests)
    send_email('copied lab tests')

@timing
def copy_observations():
    cwd = os.getcwd()
    obs_columns = ",".join(get_csv_fields(OBSERVATIONS_CSV))
    obs_csv = os.path.join(cwd, OBSERVATIONS_CSV)
    logger.info('Copying in the observations')
    copy_in_observations = f"""
        COPY labtests_observation({obs_columns}) FROM '{obs_csv}' WITH (FORMAT csv, header);
    """
    call_db_command(copy_in_observations)
    send_email('copied observations')



class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        send_email('starting')
        logger.info('Starting')
        # Write all the columns we need out of the upstream table
        # into out table
        logger.info('Writing results')
        #write_results()
        logger.info('Writing lab_test csv')
        #write_lab_test_csv()
        logger.info('Running the delete')
        run_delete()

        logger.info('Copying in the lab tests')
        copy_lab_tests()
        logger.info('Writing the observations csv')
        #write_observation_csv()
        copy_observations()
        logger.info("Finished")
