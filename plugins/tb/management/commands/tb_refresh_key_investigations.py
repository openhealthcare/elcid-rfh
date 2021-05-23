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
            loader.refresh_future_appointment_key_investigations()
            te = time()
            time_taken = ts-te
            Fact.objects.create(
                when=timezone.now(),
                label=constants.TB_APPOINTMENT_REFRESH_TIME_FACT,
                value_float=time_taken
            )
            logger.info("tb investigations refresh completed in %2.4f" % time_taken)
        except Exception:
            msg = 'Exception in refreshing TB infestications \n {}'
            logger.error(msg.format(traceback.format_exc()))