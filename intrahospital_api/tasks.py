from __future__ import absolute_import

from celery import shared_task


@shared_task
def load(user, patient):
    from intrahospital_api import loader
    fname = loader.load_patient(patient, user)
    return fname
