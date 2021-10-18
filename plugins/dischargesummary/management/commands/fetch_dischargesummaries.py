"""
Management command to fetch discharge summaries for our patients
"""
import traceback

from django.core.management import BaseCommand
from opal.models import Patient

from plugins.dischargesummary import loader, logger


class Command(BaseCommand):

    def handle(self, *a, **k):
        loader.load_all_discharge_summaries()
