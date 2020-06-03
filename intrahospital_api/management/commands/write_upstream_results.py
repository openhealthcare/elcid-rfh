"""
Management command to write a summary of results back upstream
"""
from django.core.management.base import BaseCommand
from intrahospital_api.writeback import write_result_summary


class Command(BaseCommand):
    help = "Syncs all demographics with the Cerner upstream"

    def handle(self, *args, **options):
        write_result_summary()
