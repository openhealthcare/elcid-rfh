from __future__ import absolute_import

from celery import shared_task


@shared_task
def load(patient, patient_load):
    from intrahospital_api import loader
    fname = loader._load_patient(
        patient, patient_load
    )
    return fname
