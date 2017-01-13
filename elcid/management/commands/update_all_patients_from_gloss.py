"""
Randomise our admission dates over the last year.
"""

from elcid import gloss_api
from django.core.management.base import BaseCommand
from opal.models import Patient


class Command(BaseCommand):
    def handle(self, *args, **options):
        hospital_numbers = Patient.objects.all().values_list(
            "demographics__hospital_number"
        )
        for hospital_number in hospital_numbers:
            gloss_api.patient_query(hospital_number)
