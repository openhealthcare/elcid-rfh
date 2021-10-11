"""
Management command to fetch transfer histories
"""
import traceback
import datetime
import time
from django.utils import timezone
from django.core.management import BaseCommand
from plugins.monitoring.models import Fact
from plugins.admissions import loader, logger, constants, models


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        forty_days_ago = timezone.now() - datetime.timedelta(40)
        time_start = time.time()
        try:
            created = loader.load_transfer_history_since(forty_days_ago)
            time_end = time.time()
            Fact.objects.create(
                when=timezone.now(),
                label=constants.TRANSFER_HISTORY_LOAD_TIME_FACT,
                value_int=(time_end-time_start)
            )
            Fact.objects.create(
                when=timezone.now(),
                label=constants.TRANSFER_HISTORY_CREATED_COUNT_FACT,
                value_int=len(created)
            )
            Fact.objects.create(
                when=timezone.now(),
                label=constants.TRANSFER_HISTORY_COUNT_FACT,
                value_int=models.TransferHistory.objects.all().count()
            )
        except Exception:
            msg = "Failed to load transfer histories"
            msg += "Last exception \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
