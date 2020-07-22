"""
Management command to fetch imaging for all our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.imaging import loader, logger


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        failure_count = 0
        for patient in Patient.objects.all():
            try:
                loader.load_imaging(patient)
            except Exception:
                failure_count += 1

        if failure_count:
            msg = "Failed to load imaging for {} patients \n".format(
                failure_count
            )
            msg += "Last exception \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
