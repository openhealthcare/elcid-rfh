"""
A management command that runs every 5 mins and loads in
batches of patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.appointments import (
    update_appointments, update_all_appointments
)


class Command(BaseCommand):
    help = "updates appointments"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true'
        )

    def handle(self, *args, **options):
        if options["force"]:
            update_all_appointments()
        else:
            update_appointments()
