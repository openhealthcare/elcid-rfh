import datetime

from plugins.labtests.models import Observation
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        start = datetime.date(2026, 9, 1)

        obs = Observation.objects.filter(
            test__test_name='BLOOD CULTURE',
            observation_name='Blood Isolate(s)',
            test__datetime_ordered__gte=start
        )
        for observation in obs:
            if 'Escherichia coli' in observation.observation_value:
                print(f"{observation.test.lab_number} {observation.test.patient.demographics().hospital_number} {observation.test.datetime_ordered} {observation.observation_value}")
                print('-')
