import datetime
import time
import traceback
from django.core.management.base import BaseCommand
from django.utils import timezone
from opal.models import Patient
from intrahospital_api import update_demographics, logger, constants
from plugins.monitoring.models import Fact


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            start = time.time()
            since = timezone.now() - datetime.timedelta(2)
            upstream_merged_mrns = update_demographics.get_all_merged_mrns_since(since)
            update_demographics.check_and_handle_upstream_merges_for_mrns(upstream_merged_mrns)
            finished = time.time()
            now = timezone.now()
            minutes_taken = int(int(finished-start)/60)
            total_merge_count = Patient.objects.filter(mergedmrn__isnull=False).count()
            Fact(when=now, label=constants.MERGE_LOAD_MINUTES, value_int=minutes_taken).save()
            Fact(when=now, label=constants.TOTAL_MERGE_COUNT, value_int=total_merge_count).save()
        except Exception:
            msg = "Loading merges:  \n{}".format(traceback.format_exc())
            logger.error(msg)
            raise
        return
