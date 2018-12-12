"""
A management command that runs ones a day and
loads the demographics for all patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.services.appointments import service


class Command(BaseCommand):
    help = "Runs a batch load of appointments"

    def handle(self, *args, **options):
        service.batch_load()
