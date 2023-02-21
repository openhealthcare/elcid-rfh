from django.core.management.base import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from elcid.models import Demographics
from opal.models import Patient
from plugins.dischargesummary import loader as dicharge_summary_loader
from intrahospital_api import loader
from intrahospital_api import merge_patient
from django.db import transaction
from intrahospital_api import logger
from elcid.utils import timing

# The patient ids of patients who we want to double check before merging
COMPLEX_MERGES = set([
    "65695",
    "7958",
    "1878",
    "72281",
    "25648",
    "22235",
    "43079",
    "2244",
    "66313",
    "56979",
    "25182",
    "39646",
    "71583",
])

IPC_QUERY = """
    SELECT * FROM ElCid_Infection_Prevention_Control_View
    WHERE Patient_Number LIKE '0%'
"""

DISCHARGE_SUMMARY_QUERY = """
    SELECT DISTINCT(RF1_NUMBER)
    FROM VIEW_ElCid_Freenet_TTA_Main
    WHERE RF1_NUMBER LIKE '0%'
"""

ICU_HANDOVER = """
    SELECT DISTINCT(Patient_MRN)
    FROM VIEW_ElCid_ITU_Handover
    WHERE Patient_MRN LIKE '0%'
"""

NURSE_HANDOVER = """
    SELECT DISTINCT(Patient_MRN)
    FROM VIEW_ElCid_Nursing_Handover
    WHERE Patient_MRN LIKE '0%'
"""


def zero_prefixed_ipc():
    """
    Return all zero prefixed MRNs in the upstream IPC view
    """
    api = ProdAPI()
    query_result = api.execute_hospital_query(IPC_QUERY)
    return [i["Patient_Number"] for i in query_result]


def zero_prefixed_discharge_summaries():
    """
    Return all zero prefixed MRNs in the upstream discharge summary view
    """
    api = ProdAPI()
    query_result = api.execute_hospital_query(DISCHARGE_SUMMARY_QUERY)
    return [i["RF1_NUMBER"] for i in query_result]


def zero_prefixed_icu_handover():
    """
    Return all zero prefixed MRNs in the ICU handover view
    """
    api = ProdAPI()
    query_result = api.execute_hospital_query(ICU_HANDOVER)
    return [i["Patient_MRN"] for i in query_result]


def zero_prefixed_nurse_handover():
    """
    Return all zero prefixed MRNs in the nurse handover view
    """
    api = ProdAPI()
    query_result = api.execute_hospital_query(ICU_HANDOVER)
    return [i["Patient_MRN"] for i in query_result]


def patients_with_zero_prefixes_upstream():
    """
    Returns all patients whose MRNs begin with a zero
    in the upstream tables that contain zero prefixes
    apart from lab tests as these will be resynched seperately
    """
    zeros = set()
    queries = [
        zero_prefixed_ipc,
        zero_prefixed_discharge_summaries,
        zero_prefixed_icu_handover,
        zero_prefixed_nurse_handover,
    ]
    for query in queries:
        zeros = zeros.union(query())
    stripped_zeros = [i.lstrip("0") for i in zeros if i.lstrip("0")]
    return set(Patient.objects.filter(demographics__hospital_number__in=stripped_zeros))


@timing
@transaction.atomic
def update_patients_with_leading_zero_with_no_counter_part():
    """
    Updates all MRNs that begin with a zero where we do not have
    a matching MRN without a preceding zero.

    It updates their demographics.hospital_number to not have a
    zero prefix.
    """
    # patients with leading 0s but no duplicate, remove the 0, re-sync all upstream
    cnt = 0
    demos = Demographics.objects.filter(hospital_number__startswith="0").select_related(
        "patient"
    )
    for demo in demos:
        mrn = demo.hospital_number.lstrip("0")
        if mrn and not Demographics.objects.filter(hospital_number=mrn).exists():
            print(
                f"Changing stripping the zero from the MRN of patient id {demo.patient_id}"
            )
            demo.hospital_number = mrn
            demo.save()
            cnt += 1
    print(f"updated {cnt} patients who had no non zero")


@timing
@transaction.atomic
def merge_zero_patients():
    """
    Merge zero prefixed patients with their non zero prefixed counterparts.

    It ignores MRNs that are only made up of zeros e.g. 000

    It ignores patient ids that are complex merges that we need to manually
    watch.
    """
    demos = Demographics.objects.filter(hospital_number__startswith="0")
    for demo in demos:
        mrn = demo.hospital_number
        # Ignore MRNs with only zeros
        if not mrn.lstrip("0"):
            continue
        if demo.patient_id in COMPLEX_MERGES:
            continue
        to_demos = Demographics.objects.filter(hospital_number=mrn.lstrip("0")).first()
        if to_demos:
            from_patient = demo.patient
            to_patient = to_demos.patient
            logger.info(f"Merged {mrn}")
            merge_patient.merge_patient(
                old_patient=from_patient, new_patient=to_patient
            )


class Command(BaseCommand):
    @timing
    @transaction.atomic
    def handle(self, *args, **options):
        # We do this first as we do not need to reload these patients
        # the merge patient does this.
        merge_zero_patients()

        # We need to update all our patients beginning with zero
        patients_to_reload = set(Patient.objects.filter(demographics__hospital_number__startswith="0"))

        # We need to reload all patients where there exists a zero upstream
        patients_to_reload = patients_to_reload.union(
            patients_with_zero_prefixes_upstream()
        )

        # Unless they are in the complex patients
        patients_to_reload = [
            i for i in patients_to_reload if i.id not in COMPLEX_MERGES
        ]

        patients_to_load_count = len(patients_to_reload)
        for idx, patient in enumerate(patients_to_reload):
            print(f'loading {idx+1}/{patients_to_load_count}')
            loader.load_patient(patient, run_async=False)
            dicharge_summary_loader.load_dischargesummaries(patient)
