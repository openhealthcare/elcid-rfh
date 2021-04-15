"""
Management command to generate a weekly covid extract
"""
import traceback

from django.core.management.base import BaseCommand

from plugins.covid import extract, logger


class Command(BaseCommand):
    def handle(self, *a, **k):
        try:
            extract.generate_extract_file()
        except:
            msg = 'Exception generating weekly COVID-19 extract \n {}'
            logger.error(msg.format(traceback.format_exc()))
        return
