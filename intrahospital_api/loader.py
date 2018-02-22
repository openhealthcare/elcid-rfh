from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from intrahospital_api import models
from elcid import models as emodels
from opal.models import Patient
from intrahospital_api.apis import get_api
from intrahospital_api.exceptions import BatchLoadError


def initial_load():
    user = User.objects.get(username=settings.API_USER)
    total = Patient.objects.count()
    models.InitialPatientLoad.objects.all().delete
    for iterator, patient in enumerate(Patient.objects.all()):
        print "running {}/{}".format(iterator, total)
        load_patient(patient, user, async=False)


def load_demographics(hospital_number):
    api = get_api()
    return api.demographics(hospital_number)


def load_patient(patient, user, async=False):
    # if async api in settings is false we never
    # try and do anything asyncy
    async = async and settings.ASYNC_API
    patient_load = models.InitialPatientLoad.objects.create(
        patient=patient,
        state=models.InitialPatientLoad.RUNNING
    )
    try:
        if async:
            async_load(patient, user)
        else:
            _load_patient(patient, user)
    except:
        patient_load.state = models.InitialPatientLoad.FAILURE
        patient_load.save()
        raise
    else:
        patient_load.state = models.InitialPatientLoad.SUCCESS
        patient_load.save()


def async_load(patient, user):
    from intrahospital_api import tasks
    tasks.load.delay(user, patient)


def check_batch_load():
    if models.BatchPatientLoad.objects.filter(
        Q(stopped=None) | Q(state=models.BatchPatientLoad.RUNNING)
    ):
        raise BatchLoadError("Last load is still running")

    twenty_mins_ago = timezone.now() - timedelta(minutes=20)
    if models.BatchPatientLoad.objects.last().stop > twenty_mins_ago:
        raise BatchLoadError("Last load has not run since {}".format(
            models.BatchPatientLoad.objects.last().stop
        ))


def batch_load():
    check_batch_load()
    api = get_api()
    last_update = models.BatchPatientLoad.objects.order_by(
        "stopped"
    ).last()
    batch = models.BatchPatientLoad.objects.create(
        start=timezone.now(),
        state=models.BatchPatientLoad.RUNNING
    )

    try:
        _batch_load()
    except:
        batch.stopped = timezone.now()
        batch.status = models.BatchPatientLoad.FAILURE
    else:
        batch.stopped = timezone.now()
        batch.status = models.BatchPatientLoad.SUCCESS


@transaction.atomic
def _batch_load():
    api = get_api()
    data_deltas = api.data_deltas()
    for data_delta in data_deltas:
        demographics = data_delta["demographics"]
        # get the demographics for this patient
        patient_demographics_set = emodels.Demographics.objects.filter(
            hospital_number=demographics["hospital_number"]
        )
        # does a patient with these attributes exist
        if not patient_demographics_set.filter(
            **demographics
        ).exists():
            # if not, then we need to update
            patient_demographics = patient_demographics_set.get()
            patient_demographics.update_from_dict(
                data_delta["demographics"]
            )


def update_tests(hospital_number, lab_tests):
    """
        takes in all lab tests, saves those
        that need saving updates those that need
        updating.


    """
    upstream_lab_tests = models.UpstreamLabTest.objects.filter(
        patient__demographics__hospital_number=hospital_number
    )
    pass


@transaction.atomic
def _load_patient(patient, user):
    hospital_number = patient.demographics_set.first().hospital_number
    patient.labtest_set.filter(
        lab_test_type__in=[
            emodels.UpstreamBloodCulture.get_display_name(),
            emodels.UpstreamLabTest.get_display_name()
        ]
    ).delete()

    api = get_api()
    patient_results = api.results_for_hospital_number(
        hospital_number
    )

    dict(
        patient, patient_results, user
    )


def load_in_lab_tests(
    patient, hospital_number, user
):
    api = get_api()
    results = api.results_for_hospital_number(hospital_number)
    save_lab_tests(patient, results, user)


def save_lab_tests(patient, results, user):
    for result in results:
        result["patient_id"] = patient.id
        if result["test_name"] == "BLOOD CULTURE":
            hl7_result = emodels.UpstreamBloodCulture()
        else:
            hl7_result = emodels.UpstreamLabTest()

        hl7_result.update_from_dict(result, user)


def refresh_upstream_lab_tests(patient, user):
    hospital_number = patient.demographics_set.first().hospital_number
    patient.labtest_set.filter(
        lab_test_type__in=[
            emodels.UpstreamBloodCulture.get_display_name(),
            emodels.UpstreamLabTest.get_display_name()
        ]
    ).delete()
    load_in_lab_tests(patient, hospital_number, user)
