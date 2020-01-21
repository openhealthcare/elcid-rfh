"""
Randomise our admission dates over the last year.
"""
import datetime
from django.core.management.base import BaseCommand
from intrahospital_api.models import UpstreamLabTestRow
from intrahospital_api.apis.prod_api import ProdApi
from elcid.models import Demographics

SINCE = datetime.datetime(2020, 1, 18)


class Command(BaseCommand):

    def handle(self, *args, **options):
        api = ProdApi()
        all_rows = api.execute_trust_query(
            api.all_data_since_query,
            params=dict(since=SINCE)
        )
        for row in all_rows:
            if Demographics.objects.filter(
                hospital_number=row["Patient_Number"]
            ).exists():
                UpstreamLabTestRow.create(row)

