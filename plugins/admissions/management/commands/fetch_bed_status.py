"""
Management command to fetch upstream bed status
"""
import traceback

from django.core.management import BaseCommand

from plugins.admissions import loader, logger

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        try:
            loader.load_bed_status()
            logger.info('Success loading bed status')
        except Exception:
            msg = "Loading bed status:  \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
