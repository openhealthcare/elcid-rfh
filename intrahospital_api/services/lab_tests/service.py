import copy
from collections import defaultdict
from django.core.mail import send_mail as django_send_mail
from django.conf import settings
from django.utils import timezone
from intrahospital_api.services.base import service_utils, load_utils
from intrahospital_api import logger
from elcid import models as elcid_models
from opal import models as opal_models
from opal.core import serialization
from lab.models import LabTest
from intrahospital_api import models as intrahospital_api_models

SERVICE_NAME = "lab_tests"


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
        patients_with_hn = patients.filter(
            demographics__hospital_number=hospital_number
        )

        for patient in patients_with_hn:
            # lab tests are changed in place so
            # if there are multiple lab tests
            # for patient we need to copy them first
            lts = copy.copy(lab_tests)
            total += update_patient(patient, lts)

    return total


def lab_test_batch_load():
    started = load_utils.get_batch_start_time(SERVICE_NAME)
    patients = load_utils.get_loaded_patients()
    return update_patients(patients, started)


def refresh_patient(patient):
    patient.labtest_set.filter(lab_test_type__in=[
        elcid_models.UpstreamBloodCulture.get_display_name(),
        elcid_models.UpstreamLabTest.get_display_name()
    ]).delete()
    return update_patient(patient)


def clean_observations(observations, max_dt):
    """"
    Takes in a list of tules (obs_value, last_updated)

    This filters out any dicts where the last_updated > max_dt
    """
    result = []
    for observation in observations:
        last_updated = serialization.deserialize_datetime(
            observation[1]
        )
        if last_updated < max_dt:
            result.append(observation)

    return result


def clean_lab_tests(lab_test_number_to_observations, max_dt):
    result = dict()

    for lab_test_number, observations in lab_test_number_to_observations.items():
        cleaned_observations = clean_observations(observations, max_dt)
        if cleaned_observations:
            result[lab_test_number] = cleaned_observations
    return result


def diff_patient(patient, unclean_db_lab_tests, max_dt):
    """
    Missing lab tests are lab tests numbers that exist upstream but not locally
    Additional lab tests are lab test numbers that exist locally but not upstream
    Different observations is a dict
    {
        {{ lab_number }}: missing_observations: set([{{ observation value }}, {{ last_updated}}]),
                          additional_observations: set([{{ observation value }}, {{ last_updated}}])
    }

    """
    result = dict(
        missing_lab_tests=[],
        additional_lab_tests=[],
        different_observations={},
    )
    lab_tests = patient.labtest_set.filter(
        lab_test_type__istartswith="upstream"
    )

    lab_test_number_to_summaries = defaultdict(list)

    for lab_test in lab_tests:
        observations = lab_test.extras["observations"]
        summaries = [
            (i["observation_value"], i["last_updated"],) for i in observations
        ]
        lab_test_number_to_summaries[
            lab_test.external_identifier
        ].extend(summaries)

    lab_test_number_to_summaries = clean_lab_tests(
        lab_test_number_to_summaries, max_dt
    )
    db_lab_tests = clean_lab_tests(unclean_db_lab_tests, max_dt)
    our_lab_test_numbers = set(lab_test_number_to_summaries.keys())

    db_lab_test_numbers = set(db_lab_tests.keys())
    result["missing_lab_tests"] = db_lab_test_numbers - our_lab_test_numbers
    result["additional_lab_tests"] = our_lab_test_numbers - db_lab_test_numbers
    lab_test_results = dict()

    for lab_test_number, our_summaries in lab_test_number_to_summaries.items():

        if lab_test_number in result["additional_lab_tests"]:
            continue

        db_summaries = set(db_lab_tests[lab_test_number])

        # for the moment we don't record additional observations
        # as we are keeping the super set of what is upstream
        missing_observations = db_summaries - set(our_summaries)

        if missing_observations:
            lab_test_results[lab_test_number] = dict(
                missing_observations=missing_observations,
            )

    result["different_observations"] = lab_test_results

    if(any(result.values())):
        return result


def diff_patients(*patients_to_diff):
    """
    Returns a dictionary of hospital number to the output
    of diff_patient
    """
    hospital_number_to_patients = defaultdict(list)
    max_dt = timezone.now()

    for patient in patients_to_diff:
        hn = patient.demographics_set.get().hospital_number
        hospital_number_to_patients[hn].append(patient)

    api = service_utils.get_api("lab_tests")
    db_results = api.get_summaries(
        *hospital_number_to_patients.keys()
    )
    results = {}
    for hospital_number, patients in hospital_number_to_patients.items():
        for patient in patients:
            diffs = diff_patient(
                patient, db_results[hospital_number], max_dt
            )
            if diffs:
                results[hospital_number] = diffs
    return results


def send_smoke_check_results(patients_with_issues):
    issues = [
        "{}#/patient/{}".format(
            settings.DEFAULT_DOMAIN, p.id
        ) for p in patients_with_issues
    ]

    django_send_mail(
        "The Smoke Check has found {} issues".format(
            len(issues)
        ),
        "\n".join(issues),
        settings.DEFAULT_FROM_EMAIL,
        [i[1] for i in settings.ADMINS],
        html_message="<br />".join(issues)
    )


def smoke_test():
    patient_ids = intrahospital_api_models.InitialPatientLoad.objects.filter(
        state=intrahospital_api_models.InitialPatientLoad.SUCCESS
    ).values_list(
        "patient_id", flat=True
    ).distinct()

    patients = opal_models.Patient.objects.filter(id__in=patient_ids)
    hospital_number_with_issues = diff_patients(*patients).keys()
    patients_with_issues = opal_models.Patient.objects.filter(
        demographics__hospital_number__in=hospital_number_with_issues
    )

    if len(patients_with_issues) > 0:
        send_smoke_check_results(patients_with_issues)


# not an invalid, name, its not a constant, seperate out
# for testing purposes
# pylint: disable=invalid-name
batch_load = load_utils.batch_load(
    service_name=SERVICE_NAME
)(
    lab_test_batch_load
)
