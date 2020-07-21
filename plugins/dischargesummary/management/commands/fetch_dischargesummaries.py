"""
Management command to fetch discharge summaries for our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.dischargesummary import loader, logger


class Command(BaseCommand):

    def handle(self, *a, **k):
        failure_count = 0
        for patient in Patient.objects.all():
            try:
                loader.load_dischargesummaries(patient)
            except Exception:
                failure_count += 1

        if failure_count:
            msg = "Failed to load dischargesummaries for {} patients".format(
                failure_count
            )
            msg += "\nLast exception \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
