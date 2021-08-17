import time
import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from plugins.labtests.models import (
    ObservationHistory, Observation, AbstractObserveration
)
from plugins.labtests import logger


class Command(BaseCommand):
    def handle(self, *args, **options):
        start = time.time()
        to_create = []
        yesterday = timezone.now() - datetime.timedelta(1)
        obs = Observation.objects.filter(
            test__test_name__in=ObservationHistory.TEST_NAMES
        ).filter(
            created_at__gte=yesterday
        ).select_related(
            'test'
        )
        for ob in obs:
            filter_args = {
                'test_name': ob.test.test_name,
                'lab_number': ob.test.lab_number,
                'patient_id': ob.test.patient_id
            }
            for field in AbstractObserveration._meta.get_fields():
                # fields that are db populated our side we can skip
                if getattr(field, "auto_now_add", False):
                    continue
                if getattr(field, "auto_now", False):
                    continue
                field_name = field.name
                filter_args[field_name] = getattr(ob, field_name)
            if not ObservationHistory.objects.filter(
                **filter_args
            ).exists():
                to_create.append(ObservationHistory(**filter_args))
        ObservationHistory.objects.bulk_create(to_create)
        logger.info(f"created {len(to_create)} in {time.time() - start}s")
