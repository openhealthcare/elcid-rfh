import copy
from intrahospital_api.services.base import service_utils, load_utils
from intrahospital_api import logger
from elcid import models as elcid_models
from opal.models import Patient
from lab.models import LabTest

SERVICE_NAME = "lab_tests"

from intrahospital_api.services.base import service_utils
api = service_utils.get_api("lab_tests")
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
    """
    Updates all the lab tests for a queryset of patients
    since a certain time.
    """
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

        # we should never have more than one patient per hospital number
        # but it has happened
        patients = patients.filter(
            demographics__hospital_number=hospital_number
        )

        for patient in patients:
            # lab tests are changed in place so
            # if there are multiple lab tests
            # for patient we need to copy them first
            lts = copy.copy(lab_tests)
            total += update_patient(patient, lts)

    return total


import time

def time_bulk_load_query(some_query):
    test_bulks = [50, 100, 200]
    hospital_numbers = elcid_models.Demographics.objects.all().values_list(
        "hospital_number", flat=True
    )
    for test_bulk in test_bulks:
        ts = time()
        result = bulk_load_query(hospital_numbers, test_bulk)
        te = time()
        print 'result: %s rows in  %2.4f sec' % (
            len(result), te-ts
        )


def bulk_load_query(hospital_numbers, amount):
    hospital_numbers = list(hospital_numbers)
    api = service_utils.get_api("lab_tests")
    result = []
    for i in xrange(0, len(hospital_numbers), amount):
        hns = hospital_numbers[i:i+amount]
        result.extend(api.get_rows(*hns))


def diff_patient(patient, db_results):
    result = dict(
        missing_lab_tests=[],
        additional_lab_tests=[],
        additional_observations=[],
        different_observations=[],
    )
    our_lab_tests = patient.labtest_set.filter(
        lab_test_type__istartswith="upstream"
    )
    hn = patient.demographics_set.all()[0].hospital_number
    db_lab_tests = db_results[hn]

    our_lab_test_numbers = set(our_lab_tests.values_list(
        "external_identifier", flat=True
    ))

    db_lab_test_numbers = set(db_lab_tests.keys())
    result["missing_lab_tests"] = db_lab_test_numbers - our_lab_test_numbers
    result["additional_lab_tests"] = our_lab_test_numbers - db_lab_test_numbers
    lab_test_results = dict()

    for lab_test in our_lab_tests:
        ei = lab_test.external_identifier
        if ei in result["additional_lab_tests"]:
            continue

        observation_set = lab_test.extras["observations"]
        our_observations = set(
            (
                i["observation_value"], i["last_updated"],
            ) for i in observation_set
        )
        db_observations = set(db_lab_tests[ei])
        mo = db_observations - our_observations
        ao = our_observations - db_observations

        if mo or ao:
            lab_test_results[ei] = {}

            if mo:
                lab_test_results[ei]["missing_observations"] = mo

            if ao:
                lab_test_results[ei]["additional_observations"] = ao

    result["observation_diffs"] = lab_test_results

    if(any(result.values())):
        return result


def smoke_check(*patients):
    api = service_utils.get_api("lab_tests")
    hospital_numbers = elcid_models.Demographics.objects.filter(
        patient__in=patients
    ).values_list("hospital_number", flat=True)
    db_results = api.get_summaries(*hospital_numbers)
    results = {}
    for patient in patients:
        hn = patient.demographics_set.all()[0].hospital_number
        diffs = diff_patient(patient, db_results)
        if diffs:
            results[hn] = diffs
    return results


def refresh_patient(patient):
    patient.labtest_set.filter(lab_test_type__in=[
        elcid_models.UpstreamBloodCulture.get_display_name(),
        elcid_models.UpstreamLabTest.get_display_name()
    ]).delete()
    return update_patient(patient)


def lab_test_batch_load():
    started = load_utils.get_batch_start_time(SERVICE_NAME)
    patients = load_utils.get_loaded_patients()
    return update_patients(patients, started)



# not an invalid, name, its not a constant, seperate out
# for testing purposes
# pylint: disable=invalid-name
batch_load = load_utils.batch_load(
    service_name=SERVICE_NAME
)(
    lab_test_batch_load
)
