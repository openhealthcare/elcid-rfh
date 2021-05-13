from plugins.labtests import models as lab_test_models
from intrahospital_api import get_api

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
        obs = []
        for observation in lab_test_dict["observations"]:
            if any(v for i, v in observation.items() if not i == "last_updated"):
                obs.append(observation)
        lab_test_dict["observations"] = obs
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
    """"
    Lab tests should be unique for lab_number, test
    name and patient. So if we have a new on coming
    in, delete the existing one and create a new test.
    """

    lab_test_models.LabTest.objects.filter(
        lab_number=lab_test["external_identifier"],
        test_name=lab_test["test_name"],
        patient=patient
    ).delete()
    test = lab_test_models.LabTest()
    test.create_from_api_dict(patient, lab_test)
    return test

