"""
A management command that loads in some json
as outputted by the prod api
"""
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from opal import models
from intrahospital_api import update_lab_tests


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('patient_id', type=int)
        parser.add_argument('file_name', type=str)

    @transaction.atomic
    def process(self, patient, results):
        patient.lab_tests.all().delete()
        update_lab_tests.update_tests(patient, results)

    def handle(self, patient_id, file_name, *args, **options):
        # we assume that there is a user called super
        # which there won't be on prod, but we shouldn't
        # be running this on prod
        with open(file_name) as f:
            results = json.load(f)
        patient = models.Patient.objects.get(id=patient_id)
        self.process(patient, results)
        print("success")
