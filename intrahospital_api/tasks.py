from __future__ import absolute_import

from celery import shared_task


@shared_task
def load(patient, patient_load):
    from intrahospital_api import loader
    fname = loader.async_load_patient(
        patient.id, patient_load.id
    )
    return fname
