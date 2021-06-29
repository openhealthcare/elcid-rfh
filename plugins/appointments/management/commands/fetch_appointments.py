"""
Management command to fetch appointments for all our patients
"""
import traceback
import datetime
import time
from django.utils import timezone
from django.core.management import BaseCommand
from plugins.monitoring.models import Fact
from plugins.appointments import loader, logger, constants, models


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        two_days_ago = timezone.now() - datetime.timedelta(2)
        time_start = time.time()
        try:
            created = loader.load_appointments_since(two_days_ago)
            time_end = time.time()
            Fact.objects.create(
                when=timezone.now(),
                label=constants.APPOINTMENTS_LOAD_TIME_FACT,
                value_int=(time_end-time_start)
            )
            Fact.objects.create(
                when=timezone.now(),
                label=constants.APPOINTMENTS_LOAD_CREATED_COUNT_FACT,
                value_int=len(created)
            )
            Fact.objects.create(
                when=timezone.now(),
                label=constants.APPOINTMENTS_LOAD_PATIENT_COUNT_FACT,
                value_int=models.PatientImagingStatus.objects.all().count()
            )
            Fact.objects.create(
                when=timezone.now(),
                label=constants.APPOINTMENTS_COUNT_FACT,
                value_int=models.Imaging.objects.all().count()
            )
        except Exception:
            msg = "Failed to load appointments"
            msg += "Last exception \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
