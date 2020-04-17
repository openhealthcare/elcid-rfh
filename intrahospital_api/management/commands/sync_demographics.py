"""
A management command that is run by a cron job
to run intrahospital_api.update_demographics.update_all_demographics
"""
from django.core.management.base import BaseCommand
from intrahospital_api.update_demographics import update_all_demographics


class Command(BaseCommand):
    help = "Syncs all demographics with the Cerner upstream"

    def handle(self, *args, **options):
        update_all_demographics()
