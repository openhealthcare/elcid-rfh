"""
Given a ward name, load meds for patients on that ward
"""

from django.core.management.base import BaseCommand
from elcid.utils import find_patients_from_mrns
from plugins.epma import loader
from opal.models import Patient

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('ward', nargs='+')

    def handle(self, *args, **options):
        ward = options.get('ward')
        patients = Patient.objects.filter(bedstatus__ward_name=ward)
        mrns = [p.demographics().hospital_number for p in patients]

        for idx, mrn in enumerate(mrns):
            self.stdout.write(f"Looking at {mrn}, {idx+1}/{len(mrns)}")
            patient = find_patients_from_mrns([mrn])[mrn]
            loader.load_meds_for_patient(patient)
