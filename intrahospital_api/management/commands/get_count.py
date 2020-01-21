"""
Randomise our admission dates over the last year.
"""
import datetime
from django.core.management.base import BaseCommand
from intrahospital_api.models import InitialPatientLoad
from intrahospital_api.apis.prod_api import ProdApi, db_retry
from elcid.models import Demographics

SINCE = datetime.datetime(2020, 1, 18)


class Command(BaseCommand):
    @db_retry
    def run_query(self, demographics):
        api = ProdApi()
        query = "SELECT count(*) FROM tQuest.Pathology_Result_View WHERE Patient_Number = \
@hospital_number AND date_inserted > @since;"
        return api.execute_trust_query_2(
            query,
            params=dict(
                since=SINCE,
                hospital_number=demographics.hospital_number
            )
        )[0][0]

    def handle(self, *args, **options):
        result = 0
        for demographics in Demographics.objects.all():
            result += self.run_query(demographics)

        print(result)
