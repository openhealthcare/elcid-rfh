"""
Syncs all old style tests with new style tests
"""
from django.db import transaction
from django.core.management.base import BaseCommand
from plugins.labtests import models as new_lab_models
from lab import models as old_lab_models
from opal.models import Patient


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        # freezing was happening when looking at all lab tests at once
        # so we are cutting by patient
        for patient in Patient.objects.all():
            lab_tests = old_lab_models.LabTest.objects.filter(
                patient=patient
            )
            lab_tests = lab_tests.filter(
                lab_test_type__istartswith="up"
            )
            processed_lab_numbers = new_lab_models.LabTest.objects.values_list(
                "lab_number", flat=True
            )
            lab_tests = lab_tests.exclude(
                external_identifier__in=processed_lab_numbers
            )
            for lab_test in lab_tests:
                print("processing {}".format(lab_test.external_identifier))
                new_lab_models.LabTest.create_from_old_test(lab_test)

