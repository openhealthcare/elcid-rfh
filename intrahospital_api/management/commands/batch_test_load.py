"""
A management command that runs every hour and loads in
lab tests of patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.services.lab_tests import service


class Command(BaseCommand):
    help = " runs a batch load since the last successful batch run. --force\
skips sanity checks"

    def handle(self, *args, **options):
        service.batch_load()
