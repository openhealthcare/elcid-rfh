from elcid import models as emodels
from plugins.labtests import models as lab_test_models
from elcid.utils import timing
from intrahospital_api import get_api

api = get_api()


def update_tests(patient, lab_tests):
    """
    takes in all lab tests, saves those
    that need saving updates those that need
    updating.
    """
    for lab_test in lab_tests:
        lab_model = get_model_for_lab_test_type(patient, lab_test)
        get_or_create_lab_test(patient, lab_test)
        lab_model.update_from_api_dict(patient, lab_test, api.user)


def get_model_for_lab_test_type(patient, lab_test):
    if lab_test["test_name"] == "BLOOD CULTURE":
        mod = emodels.UpstreamBloodCulture
    else:
        mod = emodels.UpstreamLabTest

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

def get_or_create_lab_test(patient, lab_test):
    """"
    Updates the plugins.labtest lab test if it exists
    otherwise it creates it.
    """
    lts = patient.lab_tests.filter(
        lab_number=lab_test["external_identifier"]
    ).filter(
        test_name=lab_test["test_name"]
    )

    lt = lts.first()

    exists = bool(lt)

    if not exists:
        lt = lab_test_models.LabTest()

    lt.update_from_api_dict(patient, lab_test)

    return lt, not exists

