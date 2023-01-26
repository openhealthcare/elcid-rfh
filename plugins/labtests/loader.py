from elcid import models as elcid_models
from plugins.labtests import models as lab_test_models
from intrahospital_api import get_api
from opal.core import serialization

api = get_api()


def clean_lab_test_dicts(lab_test_dicts):
    """
    If there is no test number or lab number (aka external_identifier)
    skip it.

    Exclude observations that only have an last_updated time stamp
    """
    result = []

    for lab_test_dict in lab_test_dicts:
        if not lab_test_dict["test_name"] and not lab_test_dict["external_identifier"]:
            continue
        result.append(lab_test_dict)
    return result


def update_tests(patient, lab_tests):
    """
    takes in all lab tests, saves those
    that need saving updates those that need
    updating.
    """
    lab_tests = clean_lab_test_dicts(lab_tests)
    for lab_test in lab_tests:
        delete_and_create_lab_test(patient, lab_test)


def delete_and_create_lab_test(patient, lab_test):
    """ "
    Lab tests should be unique for lab_number, test
    name and patient. So if we have a new on coming
    in, delete the existing one and create a new test.
    """

    lab_test_models.LabTest.objects.filter(
        lab_number=lab_test["external_identifier"],
        test_name=lab_test["test_name"],
        patient=patient,
    ).delete()
    test = lab_test_models.LabTest()
    test.create_from_api_dict(patient, lab_test)
    return test


def clean_queryset(queryset):
    result = []
    for row in queryset:
        # If there is no hospital_number skip it
        if not row["demographics"]["hospital_number"].strip():
            continue
        cleaned_lab_tests = []
        for lab_test in row["lab_tests"]:
            # if there is no lab number skip it
            if not lab_test["external_identifier"]:
                continue
            # if there is no test name skip it
            if not lab_test["test_name"]:
                continue
            cleaned_lab_tests.append(lab_test)
        row["lab_tests"] = cleaned_lab_tests
        result.append(row)
    return result


def remove_non_elcid_patients(queryset, our_hospital_numbers):
    result = []
    for row in queryset:
        hospital_number = row["demographics"]["hospital_number"]
        if hospital_number in our_hospital_numbers:
            result.append(row)
    return result


def cast_to_lab_test(patient_id, lab_test_dict):
    lab_test = lab_test_models.LabTest()
    lab_test.patient_id = patient_id
    lab_test.clinical_info = lab_test_dict["clinical_info"]
    if lab_test_dict["datetime_ordered"]:
        lab_test.datetime_ordered = serialization.deserialize_datetime(
            lab_test_dict["datetime_ordered"]
        )
    lab_test.lab_number = lab_test_dict["external_identifier"]
    lab_test.status = lab_test_dict["status"]
    lab_test.test_code = lab_test_dict["test_code"]
    lab_test.site = lab_test_dict["site"]
    lab_test.test_name = lab_test_dict["test_name"]
    lab_test.accession_number = lab_test_dict["accession_number"]
    lab_test.department_int = lab_test_dict["department_int"]
    lab_test.encounter_consultant_name = lab_test_dict["encounter_consultant_name"]
    lab_test.encounter_location_name = lab_test_dict["encounter_location_name"]
    lab_test.encounter_location_code = lab_test_dict["encounter_location_code"]
    return lab_test


def cast_to_observation(observation_dict, lab_test):
    obs = lab_test_models.Observation(test=lab_test)
    obs.last_updated = serialization.deserialize_datetime(
        observation_dict["last_updated"]
    )
    if observation_dict["observation_datetime"]:
        obs.observation_datetime = serialization.deserialize_datetime(
            observation_dict["observation_datetime"]
        )
    if observation_dict["reported_datetime"]:
        obs.reported_datetime = serialization.deserialize_datetime(
            observation_dict["reported_datetime"]
        )
    fields = [
        "observation_number",
        "observation_name",
        "observation_value",
        "reference_range",
        "units",
    ]
    for f in fields:
        setattr(obs, f, observation_dict.get(f))
    return obs


def update_lab_tests_from_query(queryset):
    # remove items from the queryset that we don't care about
    queryset = clean_queryset(queryset)
    existing_hns = [i["demographics"]["hospital_number"] for i in queryset]

    hns_and_patient_ids = elcid_models.Demographics.objects.filter(
        hospital_number__in=existing_hns
    ).values_list("hospital_number", "patient_id")

    hospital_number_to_patient_id = {i: v for i, v in hns_and_patient_ids}
    queryset = remove_non_elcid_patients(
        queryset, set(hospital_number_to_patient_id.keys())
    )

    # Delete existing lab tests
    to_delete = []

    for row in queryset:
        hospital_number = row["demographics"]["hospital_number"]
        patient_id = hospital_number_to_patient_id[hospital_number]
        for lab_test_dict in row["lab_tests"]:
            lab_number = lab_test_dict["external_identifier"]
            test_name = lab_test_dict["test_name"]
            lab_test_dict = lab_test_models.LabTest.objects.filter(
                patient_id=patient_id, lab_number=lab_number, test_name=test_name
            ).first()
            if lab_test_dict:
                to_delete.append(lab_test_dict.id)
    lab_test_models.LabTest.objects.filter(id__in=to_delete).delete()

    # Create lab tests
    lab_tests_to_create = []
    for row in queryset:
        hospital_number = row["demographics"]["hospital_number"]
        patient_id = hospital_number_to_patient_id[hospital_number]
        for lab_test_dict in row["lab_tests"]:
            lab_tests_to_create.append(cast_to_lab_test(patient_id, lab_test_dict))
    lab_tests = lab_test_models.LabTest.objects.bulk_create(lab_tests_to_create)

    # Create observations
    patient_id_lab_number_test_name = {}
    for lab_test in lab_tests:
        key = (
            lab_test.patient_id,
            lab_test.lab_number,
            lab_test.test_name,
        )
        patient_id_lab_number_test_name[key] = lab_test

    observations_to_create = []
    for row in queryset:
        hospital_number = row["demographics"]["hospital_number"]
        patient_id = hospital_number_to_patient_id[hospital_number]
        for lab_test_dict in row["lab_tests"]:
            lab_number = lab_test_dict["external_identifier"]
            test_name = lab_test_dict["test_name"]
            lab_test = patient_id_lab_number_test_name[
                (
                    patient_id,
                    lab_number,
                    test_name,
                )
            ]
            for observation_dict in lab_test_dict["observations"]:
                observation = cast_to_observation(observation_dict, lab_test)
                observations_to_create.append(observation)
            lab_tests_to_create.append(cast_to_lab_test(patient_id, lab_test_dict))
    lab_test_models.Observation.objects.bulk_create(observations_to_create)
