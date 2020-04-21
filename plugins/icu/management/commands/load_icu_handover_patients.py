"""
Management command to load ICU handover lists
"""
import traceback

from django.core.management.base import BaseCommand

from plugins.icu impoert loader, logger


class Command(BaseCommand):
    def handle(self, *a, **k):
        try:
            loader.load_icu_handover()
        except:
            msg = 'Exception loading ICU Handover Patients \n {}'
            logger.error(msg.format(traceback.format_exc()))
        return
