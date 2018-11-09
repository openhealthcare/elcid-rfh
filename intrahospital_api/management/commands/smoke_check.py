"""
    A management command that runs a smoke check and emails the
    elcid ids of the patients with issues
"""
from django.core.management.base import BaseCommand
from intrahospital_api.services.lab_tests import service
from intrahospital_api import models
from opal.models import Patient


class Command(BaseCommand):
    def handle(self, *args, **options):
        patient_ids = models.InitialPatientLoad.objects.filter(
            state="success"
        ).values_list(
            "patient_id", flat=True
        ).distinct()

        patients = Patient.objects.filter(id__in=patient_ids)
        service.
        load_tb_first = patients.filter(episode__category_name="TB").distinct()
        for patient in load_tb_first:
            load_patient(patient, async=False)

        without_tb = patients.exclude(
            id__in=load_tb_first.values_list("id", flat=True)
        )

        for patient in without_tb:
            load_patient(patient, async=False)
