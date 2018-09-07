import datetime
from django.utils.timezone import make_aware
from opal.core.serialization import deserialize_datetime
from elcid import models as emodels
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
        lab_model.update_from_api_dict(patient, lab_test, api.user)

def reconcile_counts(patient):
    upstream_tests = patient.labtest_set.filter(lab_test_type__istartswith="upstream")
    first_updated = make_aware(datetime.datetime.max)
    for lab_test in upstream_tests:
        for observation in lab_test.extras["observations"]:
            updated = deserialize_datetime(observation["last_updated"])
            if updated < first_updated:
                first_updated = updated
    lab_test_count = api.lab_test_count_for_hospital_number(patient.demographics().hospital_number, updated)
    if not lab_test_count == upstream_tests.count():
        return patient

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
