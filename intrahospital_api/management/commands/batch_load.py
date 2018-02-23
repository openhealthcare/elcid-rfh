"""
A management command that runs every 5 mins and loads in
batches of patients
"""
from django.core.management.base import BaseCommand
from intrahospital_api.loader import batch_load


class Command(BaseCommand):
    def handle(self, *args, **options):
        batch_load()
