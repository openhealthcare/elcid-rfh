"""
    A management command that runs after a deployment
    if we have not already run an initial load run one of those
    otherwise run a batch load
"""
from django.core.management.base import BaseCommand
from intrahospital_api.loader import initial_load


class Command(BaseCommand):
    def handle(self, *args, **options):
        initial_load()
