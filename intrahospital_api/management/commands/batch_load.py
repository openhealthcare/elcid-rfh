"""
A management command that runs every 5 mins and loads in
batches of patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.loader import batch_load


class Command(BaseCommand):
    help = " runs a batch load since the last successful batch run. --force\
skips sanity checks"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true'
        )

    def handle(self, *args, **options):
        batch_load(force=options["force"])
