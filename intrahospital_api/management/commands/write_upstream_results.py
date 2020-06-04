"""
Management command to write a summary of results back upstream
"""
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand

from intrahospital_api import logger
from intrahospital_api.writeback import write_result_summary


class Command(BaseCommand):
    help = "Syncs all demographics with the Cerner upstream"

    def handle(self, *args, **options):
        if settings.WRITEBACK_ON:
            try:
                write_result_summary()
            except:
                msg = 'Exception writing result summary \n {}'
                logger.error(msg.format(traceback.format_exc()))
            return
