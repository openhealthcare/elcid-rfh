import datetime

from plugins.labtests.models import Observationx
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        start = datetime.date(2026, 10, 15)

        obs = Observation.objects.filter(
            test__test_name='BLOOD CULTURE',
            observation_name='Blood Isolate(s)',
            test__datetime_ordered__gte=start
        )
        for observation in obs:
            print(observation.observation_value)
