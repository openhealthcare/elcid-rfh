"""
Sync the AMT handover list
"""
import traceback

from django.core.management.base import BaseCommand

from plugins.handover import loader, logger


class Command(BaseCommand):
    def handle(self, *a, **k):
        try:
            loader.sync_amt_handover()
        except:
            msg = 'Exception loading AMT Handover Patients \n {}'
            logger.error(msg.format(traceback.format_exc()))
        return
