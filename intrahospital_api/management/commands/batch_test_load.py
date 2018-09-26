"""
A management command that runs every hour and loads in
lab tests of patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.services.lab_tests import loads


class Command(BaseCommand):
    help = " runs a batch load since the last successful batch run. --force\
skips sanity checks"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true'
        )

    def handle(self, *args, **options):
        loads.batch_load()
