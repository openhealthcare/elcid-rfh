"""
Write upstream advice that has not been manually sent
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from intrahospital_api.epr import write_old_advice_upstream


class Command(BaseCommand):
    help = "Write advice that has not been synced to EPR to EPR"

    def handle(self, *args, **options):
        if settings.WRITEBACK_ON:
            write_old_advice_upstream()
