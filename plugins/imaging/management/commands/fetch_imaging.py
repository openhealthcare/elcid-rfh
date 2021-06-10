"""
Management command to fetch imaging for all our patients
"""
import traceback
import datetime
from django.utils import timezone
from django.core.management import BaseCommand

from plugins.imaging import loader, logger


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        two_days_ago = timezone.now() - datetime.timedelta(2)
        try:
            loader.load_imaging_since(two_days_ago)
        except Exception:
            msg = "Failed to load imaging"
            msg += "Last exception \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
