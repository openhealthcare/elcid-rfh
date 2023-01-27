import datetime
from django.utils import timezone
from elcid import models as elcid_models
from plugins.labtests import models as lab_test_models
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI


Q_GET_LAB_TESTS = """
SELECT * FROM tQuest.Pathology_Result_View
WHERE Patient_Number=@mrn
"""

Q_GET_LAB_TESTS_SINCE = """
SELECT *
FROM VIEW_ElCid_Radiology_Results
WHERE date_inserted > @date_inserted
"""


def query_for_zero_prefixed(hospital_number):
    """
    Returns zero prefixed versions of the hospital
    number if they exist in the results table.

    We do not use prefixed zeros for MRNs as we match
    the master file but the results table does, so get
    any zero prefixed MRNs included in the table for
    the MRN.
    """
    query = """
    SELECT DISTINCT Patient_Number FROM tQuest.Pathology_Result_View
    WHERE Patient_Number LIKE '%%0' + @hospital_number
    """
    api = ProdAPI()
    other_hns = api.execute_trust_query(
        query, params={"hospital_number": hospital_number}
    )
    # we know the above query may return false positives
    # e.g. if we look for 0234 it will return 20234
    return [
        i["Patient_Number"] for i in other_hns if i["Patient_Number"].lstrip('0') == hospital_number
    ]


def query_for_hospital_number(mrn):
    api = ProdAPI()
    return api.execute_trust_query(
        Q_GET_LAB_TESTS, params={"mrn": mrn}
    )


def results_for_hospital_number(hospital_number):
    """
    returns all the results for an MRN
    aggregated into labtest: observations([])
    """
    other_hns = query_for_zero_prefixed(hospital_number)
    rows = query_for_hospital_number(hospital_number)
    for other_hn in other_hns:
        rows.extend(query_for_hospital_number(other_hn))
    return rows


def load_lab_tests(patient):
    lab_test_rows = results_for_hospital_number(patient.demographics().hospital_number)
    update_lab_tests_from_query(lab_test_rows)


def get_upstream_lab_tests_since(date_inserted):
    api = ProdAPI()
    return api.execute_trust_query(
        Q_GET_LAB_TESTS_SINCE, params={"date_inserted": date_inserted}
    )


def load_lab_tests_since(date_inserted):
    lab_test_rows = get_upstream_lab_tests_since(date_inserted)
    update_lab_tests_from_query(lab_test_rows)


def get_unique_identifiers(upstream_row):
    return (
        # MRN
        upstream_row["Patient_Number"],
        # lab number
        upstream_row["Result_ID"],
        # test name
        upstream_row["OBR_exam_code_Text"],
    )


def clean_queryset(queryset):
    mrns = [i["Patient_Number"] for i in queryset if i["Patient_Number"].strip()]
    our_mrns = set(elcid_models.Demographics.objects.filter(
        hospital_number__in=mrns
    ).values_list('hospital_number', flat=True))
    result = []
    for row in queryset:
        if not all(get_unique_identifiers(row)):
            continue
        if row["Patient_Number"] not in our_mrns:
            continue
        result.append(row)
    return result


def cast_to_lab_test(row, patient_id):
    lab_test = lab_test_models.LabTest(patient_id=patient_id)
    field_mapping = lab_test_models.LabTest.UPSTREAM_FIELDS_TO_MODEL_FIELDS
    for their_field, our_field in field_mapping.items():
        value = row[their_field]
        if value and isinstance(value, datetime.datetime):
            value = timezone.make_aware(value)
        setattr(lab_test, our_field, value)

    site = row["Specimen_Site"]
    if site and "^" in site and "-" in site:
        site = site.split("^")[1].strip().split("-")[0].strip()
    lab_test.site = site

    status_abbr = row["OBX_Status"]

    if status_abbr == "F":
        status = "complete"
    else:
        status = "pending"
    lab_test.status = status
    dep = row["Department"]
    lab_test.department_int = None
    if dep:
        lab_test.department_int = int(dep)
    return lab_test


def cast_to_observation(row, lab_test_id):
    observation = lab_test_models.Observation(test_id=lab_test_id)

    field_mapping = lab_test_models.Observation.UPSTREAM_FIELDS_TO_MODEL_FIELDS
    for their_field, our_field in field_mapping.items():
        value = row[their_field]
        if value and isinstance(value, datetime.datetime):
            value = timezone.make_aware(value)
        setattr(observation, our_field, value)
    if not observation.observation_datetime and row["Request_Date"]:
        observation.observation_datetime = timezone.make_aware(row["Request_Date"])
    return observation


def update_lab_tests_from_query(queryset):
    # remove items from the queryset that we don't care about
    queryset = clean_queryset(queryset)
    existing_hns = [i["Patient_Number"] for i in queryset]

    hns_and_patient_ids = elcid_models.Demographics.objects.filter(
        hospital_number__in=existing_hns
    ).values_list("hospital_number", "patient_id")

    hospital_number_to_patient_id = {i: v for i, v in hns_and_patient_ids}

    # Delete existing lab tests
    to_delete = []

    for row in queryset:
        hospital_number = row["Patient_Number"]
        patient_id = hospital_number_to_patient_id[hospital_number]
        lab_number = row["Result_ID"]
        test_name = row["OBR_exam_code_Text"]
        lab_test = lab_test_models.LabTest.objects.filter(
            patient_id=patient_id, lab_number=lab_number, test_name=test_name
        ).first()
        if lab_test:
            to_delete.append(lab_test.id)
    lab_test_models.LabTest.objects.filter(id__in=to_delete).delete()

    # Create lab tests
    lab_tests_to_create = []
    keys = set()
    for row in queryset:
        row_key = get_unique_identifiers(row)
        if row_key in keys:
            continue
        keys.add(row_key)
        patient_id = hospital_number_to_patient_id[row["Patient_Number"]]
        lab_tests_to_create.append(cast_to_lab_test(row, patient_id))
    lab_test_models.LabTest.objects.bulk_create(lab_tests_to_create)

    # Create observations
    observations_to_create = []
    for row in queryset:
        patient_id = hospital_number_to_patient_id[row["Patient_Number"]]
        lab_number = row["Result_ID"]
        test_name = row["OBR_exam_code_Text"]
        lab_test = lab_test_models.LabTest.objects.get(
            patient_id=patient_id,
            lab_number=lab_number,
            test_name=test_name
        )
        observation = cast_to_observation(row, lab_test.id)
        observations_to_create.append(observation)
    lab_test_models.Observation.objects.bulk_create(observations_to_create)
