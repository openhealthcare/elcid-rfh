"""
Syncs all old style tests with new style tests
"""

from django.core.management.base import BaseCommand
from plugins.labtests import models
from opal.models import Patient


class Command(BaseCommand):
    def handle(self, *args, **options):
        for ut in patient.labtest_set.filter(
            lab_test_type__istartswith="up"
        ):
            if not patient.lab_tests.exist():
                LabTest.create_from_old_test(ut)
