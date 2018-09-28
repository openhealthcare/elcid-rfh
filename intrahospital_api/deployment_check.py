import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from opal.core import serialization
from opal.models import Patient
from lab import models as lmodels
from intrahospital_api import models as imodels
from intrahospital_api.services.lab_tests import service


def get_qs(some_dt):
    lab_tests = lmodels.LabTest.objects.filter(
        lab_test_type__istartswith="upstream"
    )
    recent_lab_tests = []
    for lab_test in lab_tests:
        observations = lab_test.extras["observations"]
        for observation in observations:
            last_updated_str = observation["last_updated"]
            if last_updated_str:
                last_updated = serialization.deserialize_datetime(
                    last_updated_str
                )

                if last_updated >= some_dt:
                    recent_lab_tests.append(lab_test.id)

    return lmodels.LabTest.objects.filter(
        id__in=recent_lab_tests
    )


@transaction.atomic
def check_since(some_dt):
    result = {}
    current = get_qs(some_dt)
    result = dict(current=current.count())
    current.delete()

    patients = Patient.objects.all()
    service.update_patients(patients, some_dt)
    result["now"] = get_qs(some_dt).count()
    print "=" * 10
    print result
    print "=" * 10
    raise ValueError('boom')







