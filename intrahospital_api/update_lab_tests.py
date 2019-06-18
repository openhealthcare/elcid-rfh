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
        get_or_create_lab_test(patient, lab_test)


def get_or_create_lab_test(patient, lab_test):
    """"
    Updates the plugins.labtest lab test if it exists
    otherwise it creates it.
    """

    test, created = lab_test_models.LabTest.objects.get_or_create(
        lab_number=lab_test["external_identifier"],
        test_name=lab_test["test_name"],
        patient=patient
    )
    test.update_from_api_dict(patient, lab_test)
    return test, created


