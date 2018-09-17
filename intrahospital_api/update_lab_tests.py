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

def get_first_updated(lab_tests):
    first_updated = make_aware(datetime.datetime.max)
    for lab_test in lab_tests:
        for observation in lab_test.extras["observations"]:
            updated = deserialize_datetime(observation["last_updated"])
            if updated < first_updated:
                first_updated = updated
    return first_updated

def get_first_update_for_patient(patient):
    upstream_tests = patient.labtest_set.filter(lab_test_type__istartswith="upstream")
    return get_first_updated(upstream_tests)


def reconcile_lab_test_counts(patient):
    updated = get_first_update_for_patient(patient)
    lab_test_count = api.lab_test_count_for_hospital_number(patient.demographics().hospital_number, updated)
    if not lab_test_count == upstream_tests.count():
        return patient

def reconcile_observation_counts(patient):
    updated = get_first_update_for_patient(patient)
    upstream_count = api.observations_count_for_hospital_number(patient.demographics().hospital_number, updated)
    our_lab_tests = patient.labtest_set.filter(lab_test_type__istartswith="upstream")
    our_observation_count = sum([len(i.extras["observations"]) for i in our_lab_tests])

    if not our_observation_count == upstream_count:
        return patient, our_observation_count, upstream_count


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
