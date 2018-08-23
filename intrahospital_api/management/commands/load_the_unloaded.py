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
        load_tb_first = patients.filter(episode__category_name="TB").distinct()
        for patient in load_tb_first:
            load_patient(patient, async=False)

        without_tb = patients.exclude(
            id__in=load_tb_first.values_list("id", flat=True)
        )

        for patient in without_tb:
            load_patient(patient, async=False)
