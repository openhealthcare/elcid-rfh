import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from intrahospital_api import update_demographics


class Command(BaseCommand):
    def handle(self, *args, **options):
        since = timezone.now() - datetime.timedelta(2)
        upstream_merged_mrns = update_demographics.get_all_merged_mrns_since(since)
        update_demographics.check_and_handle_upstream_merges_for_mrns(upstream_merged_mrns)
