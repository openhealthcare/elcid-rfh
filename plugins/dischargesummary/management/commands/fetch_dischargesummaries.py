"""
Management command to fetch discharge summaries for our patients
"""
import traceback
import datetime
import time
from django.core.management import BaseCommand
from django.utils import timezone
from plugins.dischargesummary import loader, logger, constants
from plugins.dischargesummary.models import (
    DischargeMedication, DischargeSummary
)
from plugins.monitoring.models import Fact


class Command(BaseCommand):

    def handle(self, *a, **k):
        three_days_ago = datetime.date.today() - datetime.timedelta(3)
        time_start = time.time()
        try:
            loader.load_discharge_summaries_since(three_days_ago)
            time_end = time.time()
            now = timezone.now()
            Fact.objects.create(
                when=now,
                label=constants.DISCHARGE_SUMMARY_LOAD_FACT,
                value_int=(time_end-time_start)
            )
            Fact.objects.create(
                when=now,
                label=constants.TOTAL_DISCHARGE_SUMMARIES,
                value_int=DischargeSummary.objects.all().count()
            )
            Fact.objects.create(
                when=now,
                label=constants.TOTAL_DISCHARGE_MEDICATIONS,
                value_int=DischargeMedication.objects.all().count()
            )
        except Exception:
            msg = "Failed to load discharge summaries"
            msg += "Last exception \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
