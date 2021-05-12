from plugins.labtests import models as lab_test_models
from intrahospital_api import get_api

api = get_api()

def delete_lab_test(patient, lab_test_dict):
    lab_test_models.LabTest.objects.filter(
        lab_number=lab_test_dict["external_identifier"],
        test_name=lab_test_dict["test_name"],
        patient=patient
    ).delete()


def update_tests(patient, lab_tests):
    """"
    Lab tests should be unique for lab_number, test
    name and patient. So if we have a new on coming
    in, delete the existing one and create a new test.
    """
    lab_test_key_to_lab_test = {}
    for lab_test_dict in lab_tests:
        delete_lab_test(patient, lab_test_dict)
        key = (patient, lab_test_dict["external_identifier"], lab_test_dict["test_name"],)
        lab_test_key_to_lab_test[key] = lab_test_models.LabTest.translate_to_object(
            patient, lab_test_dict
        )

    lab_test_models.LabTest.objects.bulk_create(lab_test_key_to_lab_test.values())
    observations = []

    for lab_test_dict in lab_tests:
        for obs_dict in lab_test_dict["observations"]:
            key = (patient, lab_test_dict["external_identifier"], lab_test_dict["test_name"],)
            lab_test = lab_test_key_to_lab_test[key]
            observation = lab_test_models.Observation.translate_to_object(
                obs_dict
            )
            observation.test = lab_test
            observations.append(observation)

    lab_test_models.Observation.objects.bulk_create(observations)

