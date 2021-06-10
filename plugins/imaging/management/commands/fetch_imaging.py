"""
Management command to fetch imaging for all our patients
"""
import traceback
import datetime
import time
from django.utils import timezone
from django.core.management import BaseCommand
from plugins.monitoring.models import Fact
from plugins.imaging import loader, logger, constants


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        two_days_ago = timezone.now() - datetime.timedelta(2)
        time_start = time.time()
        try:
            loader.load_imaging_since(two_days_ago)
            time_end = time.time()
            Fact.objects.create(
                when=timezone.now(),
                label=constants.IMAGING_LOAD_TIME_FACT,
                value_int=(time_end-time_start)/60
            )
        except Exception:
            msg = "Failed to load imaging"
            msg += "Last exception \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
