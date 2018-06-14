from __future__ import absolute_import

from celery import shared_task


@shared_task
def load(patient_id, patient_load_id):
    from intrahospital_api import loader
    fname = async_load_patient(
        patient_id, patient_load_id
    )
    return fname
