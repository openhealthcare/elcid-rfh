from intrahospital_api.services.base import service_utils
from intrahospital_api import logger
from elcid import models as elcid_models


def lab_tests_for_hospital_number(hospital_number):
    return service_utils.get_api("lab_tests").lab_tests_for_hospital_number(
        hospital_number
    )


def get_model_for_lab_test_type(patient, lab_test):
    if lab_test["test_name"] == "BLOOD CULTURE":
        mod = elcid_models.UpstreamBloodCulture
    else:
        mod = elcid_models.UpstreamLabTest

    external_identifier = lab_test["external_identifier"]
    lab_test_type = lab_test["test_name"]
    filtered = mod.objects.filter(
        external_identifier=external_identifier,
        patient=patient
    )
    by_test_type = [
        f for f in filtered if f.extras["test_name"] == lab_test_type
    ]

    if len(by_test_type) > 1:
        raise ValueError(
            "multiple test types found for {} {}".format(
                external_identifier, lab_test_type
            )
        )

    if by_test_type:
        return by_test_type[0]
    else:
        return mod()


def update_patient(patient, lab_tests=None):
    """
    Takes in all lab tests, saves those
    that need saving updates those that need
    updating.
    """
    api = service_utils.get_api("lab_tests")
    user = service_utils.get_user()
    if lab_tests is None:
        lab_tests = api.lab_tests_for_hospital_number(
            patient.demographics_set.first().hospital_number
        )

    for lab_test in lab_tests:
        lab_model = get_model_for_lab_test_type(patient, lab_test)
        lab_model.update_from_api_dict(patient, lab_test, user)
    return len(lab_tests)


def update_patients(patients, since):
    api = service_utils.get_api("lab_tests")
    hospital_numbers = patients.values_list(
        'demographics__hospital_number', flat=True
    )
    hospital_number_to_lab_tests = api.lab_test_results_since(
        hospital_numbers, since
    )
    total = 0

    for hospital_number, lab_tests in hospital_number_to_lab_tests.items():
        logger.info(
            'updating patient results for {}'.format(hospital_number)
        )
        patient = patients.get(demographics__hospital_number=hospital_number)
        total += update_patient(patient, lab_tests)

    return total


def refresh_patient_lab_tests(patient):
    patient.labtest_set.filter(lab_test_type__in=[
        elcid_models.UpstreamBloodCulture.get_display_name(),
        elcid_models.UpstreamLabTest.get_display_name()
    ]).delete()
    return update_patient(patient)


