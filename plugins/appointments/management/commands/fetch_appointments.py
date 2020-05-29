t"""
Management command to fetch all appointments for our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.appointments import loader, logger


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for patient in Patient.objects.all():
            try:
                loader.load_appointments(patient)
            except:
                msg = 'Exception loading Appointments \n {}'
                logger.error(msg.format(traceback.format_exc()))
        return
