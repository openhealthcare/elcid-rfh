"""
Load admissions from upsteam
"""
import datetime
from collections import defaultdict
import time

from django.db import transaction
from django.db.models import DateTimeField
from django.utils import timezone
from opal.models import Patient

from elcid.episode_categories import InfectionService
from elcid.models import Demographics
from elcid.utils import find_patients_from_mrns
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.admissions.models import Encounter, PatientEncounterStatus, TransferHistory, BedStatus
from plugins.admissions import logger


# UPDATED_DATE is the max of TRANS_UPDATED
# and SPELL_UPDATED
Q_GET_TRANSFERS_SINCE = """
    SELECT *
    FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE
    UPDATED_DATE >= @since
    AND LOCAL_PATIENT_IDENTIFIER is not null
    AND LOCAL_PATIENT_IDENTIFIER <> ''
"""

Q_GET_TRANSFERS_FOR_MRN = """
    SELECT *
    FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE
    LOCAL_PATIENT_IDENTIFIER = @mrn
"""

Q_GET_RECENT_ENCOUNTERS = """
SELECT *
FROM CRS_ENCOUNTERS
WHERE
LAST_UPDATED > @timestamp
"""


Q_GET_ALL_PATIENT_ENCOUNTERS = """
SELECT *
FROM CRS_ENCOUNTERS
WHERE
PID_3_MRN = @mrn
"""

Q_GET_ALL_HISTORY = """
SELECT *
FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
"""

Q_GET_ALL_BED_STATUS = """
SELECT *
FROM INP.CURRENT_BED_STATUS
WITH (NOLOCK)
"""


def cast_to_encounter(encounter, patient):
    """
    Given a dictionary of ENCOUNTER data from the upstream database,
    and the PATIENT for whom it concerns, save it.
    """
    our_encounter = Encounter(patient=patient, upstream_id=encounter['ID'])

    for k, v in encounter.items():
        if v: # Ignore for empty / nullvalues
            # Empty is actually more complicated than pythonic truthiness.
            # Many admissions have the string '""' as the contents of room/bed
            if v == '""':
                continue

            fieldtype = type(
                Encounter._meta.get_field(Encounter.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k])
            )
            if fieldtype == DateTimeField:
                try:
                    v = timezone.make_aware(v)
                except AttributeError:
                    # Only some of the "DateTime" fields from upstream
                    # are actually typed datetimes.
                    # Sometimes (when they were data in the originating HL7v2 message),
                    # they're strings. Make them datetimes.
                    v = datetime.datetime.strptime(v, '%Y%m%d%H%M%S')
                    v = timezone.make_aware(v)

            setattr(
                our_encounter,
                Encounter.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v
            )
    return our_encounter


def update_encounters_from_query_result(rows):
    rows = [i for i in rows if is_valid_mrn(i['PID_3_MRN'])]
    from intrahospital_api.loader import create_rfh_patient_from_hospital_number
    upstream_ids = [i['ID'] for i in rows]
    existing_encounters = Encounter.objects.filter(upstream_id__in=upstream_ids)
    existing_encounters_count = existing_encounters.count()
    logger.info(f'{existing_encounters_count} existing encounters will be removed')
    mrns = [i['PID_3_MRN'].strip() for i in rows if i['PID_3_MRN'].strip()]
    mrn_to_patients = find_patients_from_mrns(mrns)
    encounters_to_create = []
    for row in rows:
        mrn = row['PID_3_MRN']
        if mrn not in mrn_to_patients:
            mrn_to_patients[mrn] = create_rfh_patient_from_hospital_number(
                mrn, InfectionService
            )
        patient = mrn_to_patients[mrn]
        encounters_to_create.append(cast_to_encounter(row, patient))
    logger.info(f'Creating {len(encounters_to_create)} encounters')
    Encounter.objects.bulk_create(encounters_to_create, batch_size=500)
    PatientEncounterStatus.objects.filter(
        patient__in=mrn_to_patients.values()
    ).update(
        has_encounters=True
    )


def load_encounters(patient):
    """
    Load any upstream admission data we may not have for PATIENT
    """
    api = ProdAPI()

    mrn = patient.demographics().hospital_number
    other_mrns = list(
        patient.mergedmrn_set.values_list('mrn', flat=True)
    )
    all_mrns = [mrn] + other_mrns
    encounters = []
    for mrn in all_mrns:
        query_result = api.execute_hospital_query(
            Q_GET_ALL_PATIENT_ENCOUNTERS,
            params={'mrn': mrn}
        )
        encounters.extend(query_result)
    update_encounters_from_query_result(encounters)


def load_excounters_since(timestamp):
    """
    Query upstream for all encounters updated in a recent period.

    Updated is either more recent, or equivalent to inserted.
    This way we catch new encounters, and updates to existing encounters
    with a single query.

    We filter the data returned from upstream against patients in the
    elCID cohort, discarding data about patients not in our cohort.

    It is unfortnately unworkably slow to either query for our patients
    by identifier.

    If the patient is one we are interested in we either create or update
    our copy of the encounter data using the upstream ID.
    """
    api = ProdAPI()

    encounters = api.execute_hospital_query(
        Q_GET_RECENT_ENCOUNTERS,
        params={'timestamp': timestamp}
    )
    update_encounters_from_query_result(encounters)


def cast_to_transfer_history(upstream_dict, patient):
    hist = TransferHistory(patient=patient)
    for k, v in upstream_dict.items():
        if not k in TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS:
            # SOURCE was added later and is not particularly interesting for us
            continue
        if v:  # Ignore empty values
            fieldtype = type(TransferHistory._meta.get_field(
                TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]
            ))
            if fieldtype == DateTimeField:
                v = timezone.make_aware(v)
            setattr(
                hist,
                TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                v
            )
    return hist


def load_transfer_history_since(since):
    api = ProdAPI()
    query_start = time.time()
    query_result = api.execute_warehouse_query(
        Q_GET_TRANSFERS_SINCE, params={"since": since}
    )
    query_end = time.time()
    query_time = query_end - query_start
    logger.info(
        f"Transfer histories: queries {len(query_result)} rows in {query_time}s"
    )
    created = create_transfer_histories(query_result)
    created_end = time.time()
    logger.info(f'Transfer histories: created {len(created)} in {created_end - query_end}')
    return created


def load_transfer_history_for_patient(patient):
    api = ProdAPI()
    mrn = patient.demographics().hospital_number
    other_mrns = list(
        patient.mergedmrn_set.values_list('mrn', flat=True)
    )
    all_mrns = [mrn] + other_mrns
    transfers = []
    for mrn in all_mrns:
        query_result = api.execute_warehouse_query(
            Q_GET_TRANSFERS_FOR_MRN,
            params={'mrn': mrn}
        )
        transfers.extend(query_result)
    created = create_transfer_histories(transfers)
    return created


def create_patients(mrns):
    """
    Create patients for the related MRNs if they do not exist.

    This is done outside a transaction to handle any race conditions
    that may exist with the transactions it spawns.
    """
    from intrahospital_api.loader import create_rfh_patient_from_hospital_number
    existing_mrns = set(Demographics.objects.filter(hospital_number__in=mrns).values_list(
        'hospital_number', flat=True
    ))
    # remove duplicates
    mrns = list(set(mrns))
    for mrn in mrns:
        if mrn not in existing_mrns:
            logger.info(f'creating {mrn}')
            create_rfh_patient_from_hospital_number(
                mrn, InfectionService, run_async=False
            )

def is_valid_mrn(mrn):
    """
    An MRN is invalid if it is None or if it is only 00s
    """
    if mrn is None:
        return False
    if len(mrn.lstrip('0').strip()) == 0:
        return False
    return True


@transaction.atomic
def create_transfer_histories(unfiltered_rows):
    from intrahospital_api.loader import create_rfh_patient_from_hospital_number
    # Remove rows where the MRN is None, an empty string or only 000s
    some_rows = [i for i in unfiltered_rows if is_valid_mrn(i['LOCAL_PATIENT_IDENTIFIER'])]
    mrns = [i['LOCAL_PATIENT_IDENTIFIER'] for i in some_rows]
    mrn_to_patients = find_patients_from_mrns(mrns)

    for mrn in mrns:
        if mrn not in mrn_to_patients:
            mrn_to_patients[mrn] = create_rfh_patient_from_hospital_number(
                mrn, InfectionService, run_async=False
            )

    slice_ids = [i["ENCNTR_SLICE_ID"] for i in some_rows]
    TransferHistory.objects.filter(
        encounter_slice_id__in=slice_ids
    ).delete()

    transfer_histories = []

    for some_row in some_rows:
        # if In_TransHist = 0 then the transmission has been deleted
        # if In_Spells = 0 then the whole spell has been deleted
        if some_row['In_TransHist'] and some_row['In_Spells']:
            patient = mrn_to_patients[some_row['LOCAL_PATIENT_IDENTIFIER']]
            transfer_histories.append(
                cast_to_transfer_history(some_row, patient)
            )
    TransferHistory.objects.bulk_create(transfer_histories)
    return transfer_histories


def load_bed_status():
    """
    Flush and re-load the upstream current_bed_status
    """
    from intrahospital_api.loader import create_rfh_patient_from_hospital_number

    api = ProdAPI()

    status = api.execute_warehouse_query(
        Q_GET_ALL_BED_STATUS
    )

    mrns = [i["Local_Patient_Identifier"] for i in status]
    mrn_to_patient = find_patients_from_mrns(mrns)

    for mrn in mrns:
        if mrn not in mrn_to_patient:
            if mrn and mrn.strip("0").strip():
                mrn_to_patient[mrn] = create_rfh_patient_from_hospital_number(
                    mrn, InfectionService
                )

    with transaction.atomic():
        BedStatus.objects.all().delete()
        for bed_data in status:
            # A bed can not have a patient, this is ok.
            patient = mrn_to_patient.get(bed_data["Local_Patient_Identifier"])
            bed_status = BedStatus(patient=patient)
            for k, v in bed_data.items():
                setattr(
                    bed_status,
                    BedStatus.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                    v
                )
            bed_status.save()
