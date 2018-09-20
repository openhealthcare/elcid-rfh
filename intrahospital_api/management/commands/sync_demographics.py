"""
A management command that syncs all demographics with upstream
"""
from django.core.management.base import BaseCommand
from intrahospital_api import demographics


class Command(BaseCommand):
    help = "sync all demographcis with upstream"

    def handle(self, *args, **options):
        demographics.sync_demographics()
