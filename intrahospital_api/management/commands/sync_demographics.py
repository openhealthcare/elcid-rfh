"""
A management command that is run by a cron job
to run intrahospital_api.update_demographics.sync_recent_patient_information
"""
import traceback
from django.core.management.base import BaseCommand
from intrahospital_api.update_demographics import sync_recent_patient_information
from intrahospital_api import logger


class Command(BaseCommand):
    help = "Syncs all demographics with the Cerner upstream"

    def handle(self, *args, **options):
        try:
            sync_recent_patient_information()
        except Exception:
            msg = f'Exception writing patient information \n {traceback.format_exc()}'
            logger.error(msg)
