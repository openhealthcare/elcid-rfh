from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from intrahospital_api import models
from elcid import models as emodels
from opal.models import Patient
from intrahospital_api.apis import get_api


def initial_load():
    user = User.objects.get(username=settings.API_USER)
    total = Patient.objects.count()
    models.PatientLoad.objects.all().delete
    for iterator, patient in enumerate(Patient.objects.all()):
        print "running {}/{}".format(iterator, total)
        load_patient(patient, user)


def load_demographics(hospital_number):
    api = get_api()
    return api.demographics(hospital_number)


def load_patient(patient, user):
    patient_load = models.PatientLoad.objects.create(
        patient=patient,
        state=models.PatientLoad.RUNNING
    )
    try:
        _load_patient(patient, user)
    except:
        patient_load.state = models.PatientLoad.FAILURE
        patient_load.save()
        raise
    else:
        patient_load.delete()


def async_load(patient, user):
    from intrahospital_api import tasks
    tasks.load.delay(user, patient)


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

    save_lab_tests(
        patient, patient_results, user
    )


def load_in_lab_tests(
    patient, hospital_number, user
):
    api = get_api()
    results = api.results_for_hospital_number(hospital_number)
    emodels.save_lab_tests(patient, results, user)


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
