"""
Management command to fetch all encounters for our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.admissions import loader, logger


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        try:
            loader.load_recent_encounters()
        except Exception:
            msg += "Loading encounters:  \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
