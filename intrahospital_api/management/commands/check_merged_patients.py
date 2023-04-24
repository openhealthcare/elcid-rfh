"""
Checks that our Merged MRN cron job is running.

* check_all_merged_mrns
Compares Inactive MRNs against our MergedMRN mrns
Compares Active MRNs to Demographics hospital numbers which have related MRNs
Sends an email if we are missing MRNs.
"""
from django.core.management.base import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from elcid import models as elcid_models
from intrahospital_api import logger
from django.core.mail import send_mail
from django.conf import settings

INACTIVE_IDS_TO_IGNORE = [
    3382209,  # Inactive, merged with 2 MRNs, both marked as active
    3410891,  # Merged with an active MRN, but the active MRN has no merge comment
    3453183,  # Inactive, merged with 2 MRNs, both marked as active
    3377689,  # Inactive, merged with 2 MRNs, both marked as active
]


GET_ALL_MERGED_PATIENTS = """
    SELECT ID, PATIENT_NUMBER, ACTIVE_INACTIVE FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
"""


def send_email(title):
    title = f"{settings.OPAL_BRAND_NAME}: {title}"
    send_mail(
        title,
        "",
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMINS,
    )



def get_all_merged_patients():
    api = ProdAPI()
    return api.execute_hospital_query(GET_ALL_MERGED_PATIENTS)


def check_all_merged_mrns():
    """
    Checks all patients who are marked as merged in the upstream.

    If patients are inactive, it makes sure we have mergedMRNs. It ignores
    CRS Masterfile rows with ids declared in INACTIVE_IDS_TO_IGNORE

    If patients are active it makes sure we have Demographics with those
    MRNs and that the patients have merged MRNs.
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
        send_email(f"{len(intersection)} MRN(s) are in the MergedMRN table AND Demographics")
        logger.info(f"{len(intersection)} MRN(s) are in the MergedMRN table AND Demographics ({intersection})")
        return
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
        send_email(f"We have {len(missing_active)} missing active MRN(s)")

    # We have patients in elCID that are not marked as merged
    # but should are merged in the upstream table.
    if len(missing_inactive) > 0:
        logger.info(f"Missing inactive MRNs {missing_inactive}")
        send_email(f"We have {len(missing_inactive)} missing inactive MRN(s)")


class Command(BaseCommand):
    def handle(self, *args, **options):
        check_all_merged_mrns()
