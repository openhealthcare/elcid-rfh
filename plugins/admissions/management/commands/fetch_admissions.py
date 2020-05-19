"""
Management command to fetch all encounters for our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.admissions import loader, logger


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for patient in Patient.objects.all():
            try:
                loader.load_encounters(patient)
            except:
                msg = 'Exception loading admissions \n {}'
                logger.error(msg.format(traceback.format_exc()))
        return
