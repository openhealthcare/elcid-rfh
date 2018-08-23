"""
    A management command that loads tests for
    everyone without an Initial Patient Load
"""
from django.core.management.base import BaseCommand
from opal.models import Patient
from intrahospital_api.loader import load_patient
from intrahospital_api import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        ipls = models.InitialPatientLoad.objects.filter(
            state="success"
        ).values_list(
            "patient_id", flat=True
        ).distinct()
        patients = Patient.objects.exclude(id__in=ipls)
        for patient in patients:
            load_patient(patient, async=False)
