"""
Creates new TB patients if they have an upcoming
appointment.

Creates a TBPatient object for each of the
patients on the TB clinic list that tells
us when the patient first became TB/NTM positive
"""
import traceback
from django.utils import timezone
from django.core.management.base import BaseCommand
from plugins.monitoring.models import Fact
from plugins.tb import loader, logger, constants
from time import time


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            ts = time()
            loader.refresh_tb_patients()
            te = time()
            time_taken = ts-te
            Fact.objects.create(
                when=timezone.now(),
                label=constants.TB_REFRESH_TIME_FACT,
                value_float=time_taken
            )
            logger.info("tb refresh completed in %2.4f" % time_taken)
        except Exception:
            msg = 'Exception in refreshing TB appointments \n {}'
            logger.error(msg.format(traceback.format_exc()))

