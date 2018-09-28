import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from opal.core import serialization
from opal.models import Patient
from lab import models as lmodels
from intrahospital_api import models as imodels
from intrahospital_api.services.lab_tests import service


def get_qs(min_dt, max_dt=None):
    lab_tests = lmodels.LabTest.objects.filter(
        lab_test_type__istartswith="upstream"
    )
    recent_lab_tests = []
    max_updated = datetime.datetime.min()
    if max_dt is None:
        max_dt = datetime.datetime.max()

    for lab_test in lab_tests:
        observations = lab_test.extras["observations"]
        for observation in observations:
            last_updated_str = observation["last_updated"]
            if last_updated_str:
                last_updated = serialization.deserialize_datetime(
                    last_updated_str
                )
                if max_updated < last_updated:
                    max_updated = last_updated

                if last_updated >= min_dt and last_updated <= max_dt:
                    recent_lab_tests.append(lab_test.id)

    return lmodels.LabTest.objects.filter(
        id__in=recent_lab_tests
    ), max_updated


@transaction.atomic
def check_since(some_dt):
    result = {}
    current, max_updated = get_qs(some_dt)
    patient_ids = current.values_list('patient_id', flat=True)
    result = dict(current=current.count())
    current.delete()

    patients = Patient.objects.all()
    service.update_patients(patients, some_dt)
    batch_load, _ = get_qs(some_dt, max_updated)
    result["batch_load"] = batch_load.count()
    batch_load.delete()

    patients = Patient.objects.filter(id__in=patient_ids)
    for patient in patients:
        service.update_patient(patient)
    initial_load, _ = get_qs(some_dt, max_updated)
    result["initial_load"] = initial_load.count()

    print "=" * 10
    print result
    print "=" * 10
    raise ValueError('boom')







