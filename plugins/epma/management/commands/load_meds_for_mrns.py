from django.core.management.base import BaseCommand
from elcid.utils import find_patients_from_mrns
from plugins.epma import loader

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('mrns', nargs='+')

    def handle(self, *args, **options):
        mrns = options.get('mrns')
        for idx, mrn in enumerate(mrns):
            self.stdout.write(f"Looking at {mrn}, {idx+1}/{len(mrns)}")
            patient = find_patients_from_mrns([mrn])[mrn]
            loader.load_meds_for_patient(patient)
