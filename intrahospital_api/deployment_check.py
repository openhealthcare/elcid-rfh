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

    max_updated = timezone.make_aware(datetime.datetime.min)
    if max_dt is None:
        max_dt = timezone.make_aware(datetime.datetime.max)

    result = {}

    for lab_test in lab_tests:
        observations = lab_test.extras["observations"]
        for observation in observations:
            last_updated_str = observation["last_updated"]
            if last_updated_str:
                last_updated = serialization.deserialize_datetime(
                    last_updated_str
                )

                if last_updated >= min_dt and last_updated <= max_dt:
                    result[observation["observation_number"]] = lab_test

                    if max_updated < last_updated:
                        max_updated = last_updated

    return result, max_updated


def get_key(observation_number, lab_test):
    return (
        observation_number, lab_test.external_identifier, lab_test.patient_id,
    )


def get_and_reset(some_dt, max_dt=None):
    obs_to_lab_test, max_updated = get_qs(some_dt, max_dt)
    values = [get_key(i, v) for i, v in obs_to_lab_test.items()]
    for lab_test in obs_to_lab_test.values():
        lab_test.delete()

    return values, max_updated


def remove_in_everything(some_list, list_1, list_2):
    """
        if an element is in some_list but not in either list_1 or list_2
        then keep it.

        Otherwise remove it
    """
    set_1 = set(list_1)
    set_2 = set(list_2)
    result = []
    for i in some_list:
        if i not in set_1 or i not in set_2:
            result.append(i)
    return result


@transaction.atomic
def check_since(some_dt, result=None):
    """
    Expects a dictionary, which it updates, then rolls back
    the transaction changes.

    This should only be run on test

    we remove duplicates across

    current is the way it is before we test the batch loads and inital loads

    the result are observations, lab number, patient id that do not exist at
    least 1 other state (be it current, post batch load or post initial load)

    the count is the total observations loaded regardless of whether
    they are in another load or not
    """

    if "test" not in settings.OPAL_BRAND_NAME.lower():
        raise ValueError('this should only be run on a test server')

    current, max_updated = get_and_reset(some_dt)
    result["current_count"] = len(current)

    # current is the output of get_key
    patient_ids = [i[-1] for i in current]

    patients = get_patients()
    service.update_patients(patients, some_dt)
    batch_load, _ = get_and_reset(some_dt, max_updated)
    result["batch_load_count"] = len(batch_load)

    for patient in patients:
        service.update_patient(patient)

    initial_load, _ = get_and_reset(some_dt, max_updated)
    result["initial_load_count"] = len(initial_load)

    result["current"] = remove_in_everything(current, batch_load, initial_load)
    result["batch_load"] = remove_in_everything(
        batch_load, current, initial_load
    )
    result["initial_load"] = remove_in_everything(
        initial_load, current, batch_load
    )
    raise RollBackError('rolling back')







