from django.utils import timezone
from django.core.management.base import BaseCommand
from plugins.monitoring.models import Fact
from plugins.tb import loader, logger, constants
from time import time


class Command(BaseCommand):
    def handle(self, *args, **options):
        ts = time()
        loader.refresh_future_tb_appointments()
        te = time()
        time_taken = ts-te
        Fact.objects.create(
            when=timezone.now(),
            label=constants.TB_APPOINTMENT_REFRESH_TIME_FACT,
            value_float=time_taken
        )
        logger.info("tb appointment refresh completed in %2.4f" % time_taken)
