"""
Checks all patients who are marked as merged in the upstream.

If those patients are merged, it makes sure they have merged MRNs
in our system.

If those patients are active, it makes sure we have active MRNs
in our system, ie patients in the demographics table that also
have entries in merged MRNs.
"""
from django.core.management.base import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from elcid.utils import timing
from elcid import models as elcid_models
from intrahospital_api import logger

MISSING_ACTIVE_THRESHOLD = 0
MISSING_INACTIVE_THRESHOLD = 3

GET_ALL_MERGED_PATIENTS = """
    SELECT Patient_Number, ACTIVE_INACTIVE FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
"""

def get_all_merged_patients():
    api = ProdAPI()
    return api.execute_hospital_query(GET_ALL_MERGED_PATIENTS)


def check():
    our_merged_mrns = set(elcid_models.MergedMRN.objects.values_list('mrn', flat=True))
    our_demographics_mrns = set(elcid_models.Demographics.objects.all().values_list('hospital_number', flat=True))
    our_merged_demographics_mrns = set(elcid_models.Demographics.objects.all().values_list(
        'hospital_number', flat=True
    ))
    intersection = our_merged_mrns.intersection(our_demographics_mrns)
    if len(intersection) > 0:
        raise ValueError(
            f"{len(intersection)} MRNS are in the MergedMRN table AND Demographics ({intersection})"
        )
    upstream_merged_rows = get_all_merged_patients()
    missing_active = []
    missing_inactive = []
    found_active = []
    found_inactive = []
    for row in upstream_merged_rows:
        mrn = row["Patient_Number"]
        if mrn not in our_merged_mrns:
            if mrn not in our_demographics_mrns:
                continue
        if row["ACTIVE_INACTIVE"] == "ACTIVE":
            if mrn not in our_merged_demographics_mrns:
                missing_active.append(mrn)
            else:
                found_active.append(mrn)
        else:
            if mrn not in our_merged_mrns:
                missing_inactive.append(mrn)
            else:
                found_inactive.append(mrn)

    # We have no Demographics.hospital_number in elCID that are active and merged upstream
    # this should never happen.
    if len(found_active) == 0:
        logger.error('We have no active merged patients in our system')
        return

    # We have no MergedMRN.mrn in elCID that are inactive and merged upstream
    if len(found_inactive) == 0:
        logger.error('We have no inactive merged patients in our system')
        return

    # We have patients in elCID that do not have merged MRNs
    # but should according to the upstream table
    if len(missing_active) > MISSING_ACTIVE_THRESHOLD:
        logger.info(f"Missing active MRNs {missing_active}")
        logger.error(f"We have {len(missing_active)} missing active MRN")

    # We have patients in elCID that are not marked as merged
    # but should are merged in the upstream table.
    if len(missing_inactive) > MISSING_ACTIVE_THRESHOLD:
        logger.info(f"Missing inactive MRNs {missing_inactive}")
        logger.error(f"We have {len(missing_inactive)} missing inactive MRN")


class Command(BaseCommand):
    def handle(self, *args, **options):
        check()
