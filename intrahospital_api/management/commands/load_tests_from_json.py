"""
A management command that loads in some json
as outputted by the prod api
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from opal import models
from elcid import models as emodels
from lab import models as lmodels
from intrahospital_api import loader


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('patient_id', type=int)
        parser.add_argument('file_name', type=str)

    def handle(self, patient_id, file_name, *args, **options):
        # we assume that there is a user called super
        # which there won't be on prod, but we shouldn't
        # be running this on prod
        user = User.objects.get(username="super")
        patient = models.Patient.objects.get(id=patient_id)
        lmodels.LabTest.objects.filter(
            patient=patient
        ).filter(
            lab_test_type__in=[
                emodels.UpstreamLabTest.get_display_name(),
                emodels.UpstreamBloodCulture.get_display_name(),
            ]
        ).delete()
        with open(file_name) as f:
            results = json.load(f)
            loader.save_lab_tests(patient, results, user)
        print "success"
