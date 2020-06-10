"""
Management command to fetch discharge summaries for our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.dischargesummary import loader, logger


class Command(BaseCommand):

    def handle(self, *a, **k):
        for patient in Patient.objects.all():
            try:
                loader.load_dischargesummaries(patient)
            except:
                msg = 'Exception loading dischargesummaries for {} \n {}'
                logger.error(msg.format(patient.id, traceback.format_exc()))
        return
