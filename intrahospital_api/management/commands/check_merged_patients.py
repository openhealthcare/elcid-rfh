"""
Checks upstream merged patients (with MRNs in elcid) are correctly
marked as merged in our system.

There are some inactive MRNs that are flawed up stream, we explicitly
ignore these based on their row "ID" column in the upstream cerner
master file table.
"""
from django.core.management.base import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from elcid import models as elcid_models
from intrahospital_api import logger

INACTIVE_IDS_TO_IGNORE = [
    3382209,  # Inactive merged with 2 MRNs, both marked as active
    3410891,  # Merged with an active MRN, but the active MRN has no merge comment
    3453183,  # Inactive merged with 2 MRNs, both marked as active
    3377689,  # Inactive merged with 2 MRNs, both marked as active
]


GET_ALL_MERGED_PATIENTS = """
    SELECT ID, PATIENT_NUMBER, ACTIVE_INACTIVE FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
"""

def get_all_merged_patients():
    api = ProdAPI()
    return api.execute_hospital_query(GET_ALL_MERGED_PATIENTS)


def check_all_merged_mrns():
    """
    Checks all patients who are marked as merged in the upstream.

    If those patients are merged, it makes sure they have merged MRNs
    in our system.

    If those patients are active, it makes sure we have active MRNs
    in our system, ie patients in the demographics table that also
    have entries in merged MRNs.
    """
    # ALL inactive MRNs
    our_merged_mrns = set(elcid_models.MergedMRN.objects.values_list('mrn', flat=True))
    # All MRNS in our system
    our_demographics_mrns = set(elcid_models.Demographics.objects.all().values_list('hospital_number', flat=True))

    # ALL active MRNs which have an inactive MRN
    our_merged_demographics_mrns = set(elcid_models.Demographics.objects.filter(
        patient_id__in=set(elcid_models.MergedMRN.objects.values_list('patient_id', flat=True).distinct())
    ).values_list(
        'hospital_number', flat=True
    ))
    intersection = our_merged_mrns.intersection(our_demographics_mrns)
    if len(intersection) > 0:
        raise ValueError(
            f"{len(intersection)} MRNS are in the MergedMRN table AND Demographics ({intersection})"
        )
    upstream_merged_rows = get_all_merged_patients()
    our_mrns = our_merged_mrns.union(our_demographics_mrns)
    upstream_merged_rows = [i for i in upstream_merged_rows if i["PATIENT_NUMBER"] in our_mrns]
    missing_active = []
    missing_inactive = []
    for row in upstream_merged_rows:
        mrn = row["PATIENT_NUMBER"]
        if row["ACTIVE_INACTIVE"] == "ACTIVE":
            if row["PATIENT_NUMBER"] not in our_merged_demographics_mrns:
                missing_active.append(mrn)
        else:
            if row["PATIENT_NUMBER"] not in our_merged_mrns:
                if row["ID"] not in INACTIVE_IDS_TO_IGNORE:
                    missing_inactive.append(mrn)

    # We have patients in elCID that do not have merged MRNs
    # but should according to the upstream table
    if len(missing_active) > 0:
        logger.info(f"Missing active MRNs {missing_active}")
        logger.error(f"We have {len(missing_active)} missing active MRN")

    # We have patients in elCID that are not marked as merged
    # but should are merged in the upstream table.
    if len(missing_inactive) > 0:
        logger.info(f"Missing inactive MRNs {missing_inactive}")
        logger.error(f"We have {len(missing_inactive)} missing inactive MRN")


class Command(BaseCommand):
    def handle(self, *args, **options):
        check_all_merged_mrns()
