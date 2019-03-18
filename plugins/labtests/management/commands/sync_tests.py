"""
Syncs all old style tests with new style tests
"""

from django.core.management.base import BaseCommand
from plugins.labtests import models
from opal.models import Patient


class Command(BaseCommand):
    def handle(self, *args, **options):
        for p in Patient.objects.all():
            models.create_from_old_tests(p)
