"""
A management command that runs every 5 mins and loads in
batches of patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.services.appointments.service import (
    update_future_appointments, update_all_appointments_in_the_last_year
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
            update_all_appointments_in_the_last_year()
        else:
            update_future_appointments()
