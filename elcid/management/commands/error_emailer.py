"""
A management command that takes in a string and sends it as an error.
"""
import logging
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, error, *args, **options):
        logger = logging.getLogger('error_emailer')
        logger.error(error)
