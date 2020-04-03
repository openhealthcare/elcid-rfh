"""
Management command to periodically re-calculate the
Covid 19 Dashboard stats.
"""
from django.core.management.base import BaseCommand
from opal.models import Patient

from plugins.covid.constants import (
    POSITIVE_TEST_VALUES, NEGATIVE_TEST_VALUES, CORONAVIRUS_TEST_NAME,
)
from plugins.covid.models import CovidDashboard


class Command(BaseCommand):

    def handle(self, *args, **options):
        CovidDashboard.objects.all().delete()
        print('Deleted Dashboard objects')

        tested = Patient.objects.filter(
            lab_tests__test_name=CORONAVIRUS_TEST_NAME).distinct()
        print('Found Tested Patients')

        positive = tested.filter(
            lab_tests__observation__observation_value__in=POSITIVE_TEST_VALUES
        )
        positive_ids = [p.id for p in positive]
        print('Found Positive Patients')

        negative = tested.filter(
            lab_tests__observation__observation_value__in=NEGATIVE_TEST_VALUES
        ).exclude(id__in=positive_ids)

        CovidDashboard.objects.create(
            patients_tested=tested.count(),
            positive=positive.count(),
            negative=negative.count()
        )
