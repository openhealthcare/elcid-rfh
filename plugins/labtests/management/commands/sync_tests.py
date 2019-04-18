"""
Syncs all old style tests with new style tests
"""
from django.db import transaction
from django.core.management.base import BaseCommand
from plugins.labtests import models as new_lab_models
from lab import models as old_lab_models


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        lab_tests = old_lab_models.LabTest.objects.filter(
            lab_test_type__istartswith="up"
        )
        processed_lab_numbers = new_lab_models.LabTest.objects.values_list(
            "lab_number", flat=True
        )
        lab_tests = lab_tests.exclude(
            external_identifier__in=processed_lab_numbers
        )
        for lab_test in lab_tests:
            new_lab_models.LabTest.create_from_old_test(lab_test)

