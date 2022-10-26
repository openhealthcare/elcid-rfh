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
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.admissions.models import Encounter, PatientEncounterStatus, TransferHistory, BedStatus
from plugins.admissions import logger


# UPDATED_DATE is the same as CREATED_DATE if there
# has not been an update, ie its always set.
Q_GET_TRANSFERS_SINCE = """
    SELECT *
    FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE
    UPDATED_DATE >= @since
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
    upstream_ids = [i['ID'] for i in rows]
    existing_encounters = Encounter.objects.filter(upstream_id__in=upstream_ids)
    existing_encounters_count = existing_encounters.count()
    logger.info(f'{existing_encounters_count} existing encounters will be removed')
    mrns = [i['PID_3_MRN'].strip() for i in rows if i['PID_3_MRN'].strip()]
    patients = Patient.objects.filter(
        demographics__hospital_number__in=mrns
    ).prefetch_related('demographics_set')

    mrn_to_patients = defaultdict(list)
    for patient in patients:
        mrn_to_patients[patient.demographics_set.all()[0].hospital_number].append(
            patient
        )

    to_create = []
    for row in rows:
        for patient in mrn_to_patients[row['PID_3_MRN'].strip()]:
            to_create.append(cast_to_encounter(row, patient))
    logger.info(f'Creating {len(to_create)} encounters')
    Encounter.objects.bulk_create(to_create, batch_size=500)
    PatientEncounterStatus.objects.filter(
        patient__in=patients
    ).update(
        has_encounters=True
    )


def load_encounters(patient):
    """
    Load any upstream admission data we may not have for PATIENT
    """
    api = ProdAPI()

    demographic     = patient.demographics()
    encounters = api.execute_hospital_query(
        Q_GET_ALL_PATIENT_ENCOUNTERS,
        params={'mrn': demographic.hospital_number}
    )
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
    from intrahospital_api.loader import create_rfh_patient_from_hospital_number
    api = ProdAPI()

    encounters = api.execute_hospital_query(
        Q_GET_RECENT_ENCOUNTERS,
        params={'timestamp': timestamp}
    )
    for encounter in encounters:
        if encounter['PID_3_MRN']:
            encounter['PID_3_MRN'] = encounter['PID_3_MRN'].strip()
    mrns = list(set([i['PID_3_MRN'] for i in encounters if i['PID_3_MRN']]))
    existing_hns = set(Demographics.objects.filter(
        hospital_number__in=mrns).values_list('hospital_number', flat=True)
    )
    for mrn in mrns:
        if mrn and mrn not in existing_hns:
            create_rfh_patient_from_hospital_number(mrn, InfectionService)
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
    created = create_transfer_histories_from_upstream_result(query_result)
    created_end = time.time()
    logger.info(f'Transfer histories: created {len(created)} in {created_end - query_end}')
    return created


def load_transfer_history_for_patient(patient):
    api = ProdAPI()
    mrn = patient.demographics().hospital_number
    query_result = api.execute_warehouse_query(
        Q_GET_TRANSFERS_FOR_MRN, params={"mrn": mrn}
    )
    created = create_transfer_histories_from_upstream_result(query_result)
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
            print(f'creating {mrn}')
            create_rfh_patient_from_hospital_number(
                mrn, InfectionService, run_async=False
            )


def create_transfer_histories_from_upstream_result(some_rows):
    create_patients([row['LOCAL_PATIENT_IDENTIFIER'] for row in some_rows])
    return create_transfer_histories(some_rows)


@transaction.atomic
def create_transfer_histories(some_rows):
    mrn_to_patients = defaultdict(list)
    demos = Demographics.objects.filter(hospital_number__in=[
        i['LOCAL_PATIENT_IDENTIFIER'] for i in some_rows
    ]).select_related('patient')
    for demo in demos:
        mrn_to_patients[demo.hospital_number].append(demo.patient)

    # This means we are already restricting the query by a index column
    # ie much faster
    existing_transfer_histories_qs = TransferHistory.objects.filter(
        patient_id__in=[demo.patient_id for demo in demos]
    )
    slice_ids = [i["ENCNTR_SLICE_ID"] for i in some_rows]
    existing_transfer_histories_qs.filter(
        encounter_slice_id__in=slice_ids
    ).delete()

    transfer_histories = []

    for some_row in some_rows:
        patients = mrn_to_patients[some_row['LOCAL_PATIENT_IDENTIFIER']]
        for patient in patients:
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

    with transaction.atomic():

        BedStatus.objects.all().delete()

        for bed_data in status:
            bed_status = BedStatus()
            for k, v in bed_data.items():
                setattr(
                    bed_status,
                    BedStatus.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                    v
                )

            if bed_status.local_patient_identifier:
                patient = Patient.objects.filter(
                    demographics__hospital_number=bed_status.local_patient_identifier
                ).first()

                if patient:
                    bed_status.patient = patient
                else:
                    patient = create_rfh_patient_from_hospital_number(
                        bed_status.local_patient_identifier, InfectionService)
                    bed_status.patient = patient

            bed_status.save()
