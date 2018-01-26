"""
A management command that loads in some json
as outputted by the prod api
"""
from django.core.management.base import BaseCommand
from intrahospital_api.loader import initial_load


class Command(BaseCommand):
    def handle(self, *args, **options):
        initial_load()
