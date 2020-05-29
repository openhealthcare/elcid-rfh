"""
Management command to pre-load Covid-19 patients
"""
from django.core.management.base import BaseCommand

from plugins.covid import logger, loader


class Command(BaseCommand):
    def handle(self, *a, **k):
        try:
            loader.pre_load_covid_patients()
        except:
            msg = 'Exception pre-loading covid patients \n {}'
            logger.error(msg.format(traceback.format_exc()))

        return
