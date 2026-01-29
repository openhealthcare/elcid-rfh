"""
Given a ward name, export Micro results as a csv
"""
from django.core.management.base import BaseCommand
from elcid.utils import find_patients_from_mrns
from plugins.research.export import write_micro_csv


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('ward', nargs='+')

    def handle(self, *args, **options):
        ward = options.get('ward')[0]
        patients = Patient.objects.filter(bedstatus__ward_name=ward)

        with open('/tmp/micro.csv', 'w') as fh:
            write_micro_csv(patients, fh)
        print('File written to /tmp/micro.csv')
