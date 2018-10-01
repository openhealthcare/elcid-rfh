import datetime
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from opal.core import serialization
from opal.models import Patient
from lab import models as lmodels
from intrahospital_api import models as imodels
from intrahospital_api.services.lab_tests import service


class RollBackError(Exception):
    pass

def get_patients():
    return Patient.objects.exclude(episode__tagging__archived=True)


def get_qs(min_dt, max_dt=None):
    patients = get_patients()
    lab_tests = lmodels.LabTest.objects.filter(
        lab_test_type__istartswith="upstream"
    ).filter(patient__in=patients)

    recent_lab_tests = []
    max_updated = timezone.make_aware(datetime.datetime.min)
    if max_dt is None:
        max_dt = timezone.make_aware(datetime.datetime.max)

    for lab_test in lab_tests:
        observations = lab_test.extras["observations"]
        for observation in observations:
            last_updated_str = observation["last_updated"]
            if last_updated_str:
                last_updated = serialization.deserialize_datetime(
                    last_updated_str
                )

                if last_updated >= min_dt and last_updated <= max_dt:
                    recent_lab_tests.append(lab_test.id)

                    if max_updated < last_updated:
                        max_updated = last_updated

    return lmodels.LabTest.objects.filter(
        id__in=recent_lab_tests
    ), max_updated


@transaction.atomic
def check_since(some_dt, result=None):
    """
    Expects a dictionary, which it updates, then rolls back
    the transaction changes.

    This should only be run on test
    """

    if "test" not in settings.OPAL_BRAND_NAME.lower():
        raise ValueError('this should only be run on a test server')
    current, max_updated = get_qs(some_dt)
    # if you don't cast this to a list it will recalculate
    # later after we have deleted the current
    # ie, patient_ids will always be empty later
    patient_ids_external_identifier = list(current.values_list('patient_id', 'external_identifier'))
    patient_ids = [i[0] for i in patient_ids_external_identifier]
    result["current"] = current.count()
    result["current_ids"] = patient_ids_external_identifier
    current.delete()

    patients = Patient.objects.filter(id__in=patient_ids)
    service.update_patients(patients, some_dt)
    batch_load, _ = get_qs(some_dt, max_updated)
    batch_load_identifiers = list(batch_load.values_list('patient_id', 'external_identifier'))
    result["batch_load_ids"] = batch_load_identifiers
    result["batch_load"] = batch_load.count()
    batch_load.delete()

    patients = Patient.objects.filter(id__in=patient_ids)

    for patient in patients:
        service.update_patient(patient)
    initial_load, _ = get_qs(some_dt, max_updated)
    intial_load_identifiers = list(initial_load.values_list('patient_id', 'external_identifier'))
    result["initial_load"] = initial_load.count()
    result["initial_load_ids"] = intial_load_identifiers

    raise RollBackError('rolling back')







