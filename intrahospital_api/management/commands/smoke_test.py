"""
    A management command that runs a smoke check and emails the
    elcid ids of the patients with issues
"""
from django.core.management.base import BaseCommand
from intrahospital_api.services.lab_tests import service
from intrahospital_api import logger


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Starting smoke test")
        service.smoke_test()
        logger.info("Smoke test complete")
