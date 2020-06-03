from __future__ import absolute_import
from intrahospital_api import logger

from celery import shared_task


@shared_task
def load(patient_id, patient_load_id):
    logger.info("starting async load patient for {} {}".format(
        patient_id, patient_load_id
    ))
    from intrahospital_api import loader
    fname = loader.async_load_patient(
        patient_id, patient_load_id
    )
    return fname

@shared_task
def write_advice_upstream(clinical_advice_id):
    logger.info(
        'Starting async advice write for advice ID {}'.format(
            clinical_advice_id
        ))
    from intrahospital_api import writeback
    writeback.write_advice_upstream(clinical_advice_id)
