from django.core.management.base import BaseCommand
from intrahospital_api import update_demographics
from elcid.utils import timing

class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        mrns = update_demographics.get_all_active_merged_mrns()
        update_demographics.check_and_handle_upstream_merges_for_mrns(mrns)
