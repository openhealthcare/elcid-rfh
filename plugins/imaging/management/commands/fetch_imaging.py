"""
Management command to fetch imagin for all our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.imaging import loader, logger


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for patient in Patient.objects.all():
            try:
                loader.load_imaging(patient)
            except:
                msg = 'Exception loading admissions for {} \n {}'
                logger.error(msg.format(patient.id, traceback.format_exc()))
        return
