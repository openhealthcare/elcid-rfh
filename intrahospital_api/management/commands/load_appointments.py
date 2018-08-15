"""
A management command that runs every 5 mins and loads in
batches of patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.update_appointments import update_appointments


class Command(BaseCommand):
    help = "updates appointments"

    def handle(self, *args, **options):
        update_appointments()
