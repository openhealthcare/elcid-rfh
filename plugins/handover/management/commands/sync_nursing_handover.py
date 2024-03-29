"""
Sync the Nursing handover list
"""
import traceback

from django.core.management.base import BaseCommand

from plugins.handover import loader, logger


class Command(BaseCommand):
    def handle(self, *a, **k):
        try:
            loader.sync_nursing_handover()
        except:
            msg = 'Exception loading Nursing Handover Patients \n {}'
            logger.error(msg.format(traceback.format_exc()))
        return
