"""
A sense check to make sure that merge_patient_since is successfully
merging patients in keeping with the upstream data.

`check_all_merged_mrns` sends_emails warning us if:
 * We have MergedMRN.mrns that are also in Demographics.hospital_number
 * We have a demographics.hospital_number that is marked as inactive upstream
 * We have a MergedMRN.mrn that is marked as active upstream
 * We have a patient with merged MRNs whose MRN is not marked as merged upstream
 * We have a MergedMRN.mrn that is not marked as inactive upstream

We are aware that the upstream data is flawed and ignore Masterfile row IDs
which we have individually validated as flawed data.
"""
from django.core.management.base import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from elcid import models as elcid_models
from elcid import utils
from intrahospital_api import logger
from django.conf import settings

INACTIVE_IDS_TO_IGNORE = [
    3382209,  # Inactive, merged with 2 MRNs, both marked as active
    3410891,  # Merged with an active MRN, but the active MRN has no merge comment
    3453183,  # Inactive, merged with 2 MRNs, both marked as active
    3377689,  # Inactive, merged with 2 MRNs, both marked as active
]

# Cerner Masterfile IDs that are of active patients where the merge
# chain does not allow us to calculate the related inactive MRNs.
# If there is no comment then it is because the id is connected to
# another active id.
ACTIVE_IDS_TO_IGNORE = [
    679807,
    707415,
    752152,
    860083,
    911946,
    848530,
    849011,
    894737,
    930420,
    950302,  # Has a merge comment, but not one related to a merge
    931464,
    933447,  # Has a merge comment, but not one related to a merge
    978465,  # Merged from an MRN that does not exist
    1102290,
    1043560,
    1113736,
    1178690,
    1260169, # Merged from an MRN that does not exist
    1230774, # Merged from an MRN that does not exist
    1281122,
    1319503, # Merged from an MRN that does not exist
    1329500,
    1309725,
    1375504,
    1401841,
    1377752,
    1403427,
    1468926,
    1418254,
    1484013,
    1498457,
    1532790,
    1473997,
    956429,
    1554569,
    1515528,
    1563315,
    1577023,
    1585428,  # Merged from an MRN that does not exist
    1561373,
    1604746,
    1649414,  # Merged from an MRN that does not exist
    1627375,
    1710609,
    1887274,  # Merged from an MRN that does not exist
    1932043,
    1978054,
    1931015,
    2093065,
    2206719,
    2254224,
    2200862,
    2368866,
    2374411,
    2365970,
    2462808,
    2504647,
    2529267,
    2609654,  # Merged from an MRN that does not exist
    2588398,  # Merged from an MRN that does not exist
    2637220,  # Merged from an MRN that does not exist
    2704228,
    2652864,
    2665117,
    2715931,
    2752599,
    2842786,
    2842787,
    2767273,  # Merged from an MRN that does not exist
    2852480,
    2900164,
    2932751,
    2987527,  # Merged from an MRN that does not exist
    3030155,
    3042202,  # Merged from an MRN that does not exist
    3267835,  # Merged from an MRN that does not exist
    3391372,
    3391416,
    3032468,
    3020341,  # Merged from an MRN that does not exist
    3274372,  # Merged from an MRN that does not exist
    3275241,  # Merged from an MRN that does not exist
    3289038,  # Merged from an MRN that does not exist
    3292901,  # Merged from an MRN that does not exist
    3312577,  # Merged from an MRN that does not exist
    3080960,
    3083371,
    3083416,
    3086786,
    3090933,
    3092753,
    3336562,
    3096519,
    3442244,
    3347982,
    3453182,
    3453370,
    3351687,
    3352883,
    3354147,
    3110007,
    3357397,
    3119062,
    3120387,
    3129535,
    3132120,  # Merged from an MRN that does not exist
    3147508,  # Merged from an MRN that does not exist
    3257202,  # Merged from an MRN that does not exist
    3267086,  # Merged from an MRN that does not exist
    1030326,
]


GET_ALL_MERGED_PATIENTS = """
    SELECT ID, PATIENT_NUMBER, ACTIVE_INACTIVE, MERGE_COMMENTS FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
"""


def get_all_merged_patients():
    api = ProdAPI()
    return api.execute_hospital_query(GET_ALL_MERGED_PATIENTS)


def check_all_merged_mrns():
    """
    Looks at all merged MRNs upstream who have are in Demographics.hospital_number
    or MergedMRN.mrn.

    Sends_emails warning us if:
    * We have a MergedMRN.mrn that are also in Demographics.hospital_number.
    * If an upstream MRN is active and merged but it is not in a list of all our Demographics.hospital numbers
      that have mergedMRNs.
    * If an upstream MRN is inactive, but they are not in our mergedMRN table.
    * If we have an active MRN with merged MRNs that is not marked as active and merged upstream.
    * If we have an inactive MRN that is not marked as inactive upstream

    Ignores CernerMasterFile rows with IDS in  that we have checked, and concluded have
    flawed data.
    """
    # ALL inactive MRNs in our system.
    our_merged_mrns = set(elcid_models.MergedMRN.objects.values_list('mrn', flat=True))
    # All demographics hospital numbers in our system whether merged or not.
    our_demographics_mrns = set(elcid_models.Demographics.objects.all().values_list('hospital_number', flat=True))

    # ALL active MRNs which have an inactive MRN.
    our_merged_demographics_mrns = set(elcid_models.Demographics.objects.filter(
        patient_id__in=set(elcid_models.MergedMRN.objects.values_list('patient_id', flat=True).distinct())
    ).values_list(
        'hospital_number', flat=True
    ))
    intersection = our_merged_mrns.intersection(our_demographics_mrns)
    if len(intersection) > 0:
        utils.send_email(f"{len(intersection)} MRN(s) are in the MergedMRN table AND Demographics", "")
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
                # At time of writing there are 24 rows with active patients
                # with null as merge comments, we can't do anything about
                # these so ignore them.
                if row["MERGE_COMMENTS"] is None:
                    continue

                # At time of writing there are 4530 rows with active patients
                # and empty merge comments, we can't do anything about
                # these so ignore them.
                if len(row["MERGE_COMMENTS"]) == 0:
                    continue
                if row["ID"] not in ACTIVE_IDS_TO_IGNORE:
                    missing_active.append(mrn)
        else:
            if row["PATIENT_NUMBER"] not in our_merged_mrns:
                if row["ID"] not in INACTIVE_IDS_TO_IGNORE:
                    missing_inactive.append(mrn)

    # We have patients in elCID that do not have merged MRNs
    # but should according to the upstream table.
    if len(missing_active) > 0:
        logger.info(f"Missing active MRNs {missing_active}")
        utils.send_email(f"We have {len(missing_active)} missing active MRN(s)", "")

    # We have patients in elCID that are not marked as merged
    # but should are merged in the upstream table.
    if len(missing_inactive) > 0:
        logger.info(f"Missing inactive MRNs {missing_inactive}")
        utils.send_email(f"We have {len(missing_inactive)} missing inactive MRN(s)", "")

    # Looks at all active MRNs in our system that have merges and makes
    # sure the upstream also has an active merge for this patient.
    active_mrns = set([row["PATIENT_NUMBER"] for row in upstream_merged_rows if row["ACTIVE_INACTIVE"] == "ACTIVE"])
    active_in_ours_but_not_in_theirs = []
    for i in list(our_merged_demographics_mrns):
        if i not in active_mrns:
            active_in_ours_but_not_in_theirs.append(i)
    if len(active_in_ours_but_not_in_theirs) > 0:
        logger.info(f"Active MRNS in ours but not in theirs {active_in_ours_but_not_in_theirs}")
        utils.send_email(f"We have {len(active_in_ours_but_not_in_theirs)} active MRN(s) that are not upstream", "")

    # Looks at all inactive MRNs in our system that have merges and makes
    # sure the upstream also has an inactive merge for this patient.
    inactive_mrns = set([row["PATIENT_NUMBER"] for row in upstream_merged_rows if row["ACTIVE_INACTIVE"] == "INACTIVE"])
    inactive_in_ours_but_not_in_theirs = []
    for i in list(our_merged_mrns):
        if i not in inactive_mrns:
            inactive_in_ours_but_not_in_theirs.append(i)
    if len(inactive_in_ours_but_not_in_theirs) > 0:
        logger.info(f"Inactive MRNS in ours but not in theirs {inactive_in_ours_but_not_in_theirs}")
        utils.send_email(f"We have {len(inactive_in_ours_but_not_in_theirs)} inactive MRN(s) that are not upstream", "")


class Command(BaseCommand):
    def handle(self, *args, **options):
        check_all_merged_mrns()
