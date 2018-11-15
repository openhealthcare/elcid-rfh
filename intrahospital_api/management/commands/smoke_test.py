"""
    A management command that runs a smoke check and emails the
    elcid ids of the patients with issues
"""
from django.core.management.base import BaseCommand
from intrahospital_api.services.lab_tests import service
from intrahospital_api import models
from opal.models import Patient


class Command(BaseCommand):
    def handle(self, *args, **options):
        service.smoke_test()
