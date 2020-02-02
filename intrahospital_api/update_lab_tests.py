from plugins.labtests import models as lab_test_models
from intrahospital_api import get_api

api = get_api()


def update_tests(patient, lab_tests):
    """
    takes in all lab tests, saves those
    that need saving updates those that need
    updating.
    """
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
    test.update_from_api_dict(patient, lab_test)
    return test

