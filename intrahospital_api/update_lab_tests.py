from elcid import models as emodels
from elcid.utils import timing
from intrahospital_api import get_api
from intrahospital_api import logger

api = get_api()


@timing
def update_tests(patient, lab_tests):
    """
        takes in all lab tests, saves those
        that need saving updates those that need
        updating.
    """
    for lab_test in lab_tests:
        lab_model = get_model_for_lab_test_type(patient, lab_test)
        logger.info("updating lab test {} for patient {}".format(
            lab_test["external_identifier"], patient.id
        ))
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
