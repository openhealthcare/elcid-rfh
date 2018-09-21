"""
A management command that loads in some json
as outputted by the prod api
"""
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from opal import models
from lab import models as lab_models
from elcid import models as elcid_models
from intrahospital_api.services.lab_tests import service as lab_tests_service


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('patient_id', type=int)
        parser.add_argument('file_name', type=str)

    @transaction.atomic
    def process(self, patient, results):
        lab_models.LabTest.objects.filter(
            patient=patient
        ).filter(
            lab_test_type__in=[
                elcid_models.UpstreamLabTest.get_display_name(),
                elcid_models.UpstreamBloodCulture.get_display_name(),
            ]
        ).delete()
        lab_tests_service.update_patient(patient, results)

    def handle(self, patient_id, file_name, *args, **options):
        # we assume that there is a user called super
        # which there won't be on prod, but we shouldn't
        # be running this on prod
        with open(file_name) as f:
            results = json.load(f)
        patient = models.Patient.objects.get(id=patient_id)
        self.process(patient, results)
        print "success"
