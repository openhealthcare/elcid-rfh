from __future__ import absolute_import

from celery import shared_task


@shared_task
def load(patient):
    from intrahospital_api import loader
    fname = loader._load_lab_tests_for_patient(patient)
    return fname
