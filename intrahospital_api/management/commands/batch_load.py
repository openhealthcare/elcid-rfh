"""
A management command that is run by a cron job every 5 mins and runs
intrahospital_api.loader.batch_load
"""
from django.core.management.base import BaseCommand
from intrahospital_api.loader import batch_load


class Command(BaseCommand):
    help = "Runs a batch load since the last successful batch run. --force\
skips sanity checks"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true'
        )

    def handle(self, *args, **options):
        batch_load(force=options["force"])
