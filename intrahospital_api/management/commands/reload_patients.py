"""
A management command that takes MRNs and reloads the
associated patients.

example calling code is

python manage.py reload_patients 234234234 12312314
"""
from django.core.management.base import BaseCommand
from opal.models import Patient
from intrahospital_api import loader


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('mrns', nargs='+')

    def handle(self, *args, **options):
        mrns = options.get('mrns')
        for idx, mrn in enumerate(mrns):
            self.stdout.write(f"Looking at {mrn}, {idx+1}/{len(mrns)}")
            patient = Patient.objects.get(demographics__hospital_number=mrn)
            loader.load_patient(patient, run_async=False)
