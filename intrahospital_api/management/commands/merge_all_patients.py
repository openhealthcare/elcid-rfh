from django.core.management.base import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api import update_demographics
from elcid.utils import timing


# Returns all active merged patients
# used by the merge_all_patients mgmt
# command
GET_ALL_ACTIVE_MERGED_MRNS = """
    SELECT Patient_Number FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
    AND ACTIVE_INACTIVE = 'ACTIVE'
"""

def get_all_active_merged_mrns():
    api = ProdAPI()
    query_result = api.execute_hospital_query(GET_ALL_ACTIVE_MERGED_MRNS)
    return [i["Patient_Number"] for i in query_result]



class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        mrns = get_all_active_merged_mrns()
        update_demographics.check_and_handle_upstream_merges_for_mrns(mrns)
