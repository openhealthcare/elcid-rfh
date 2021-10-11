"""
Load admissions from upsteam
"""
import datetime
import time
from django.db import transaction

from django.db.models import DateTimeField
from django.utils import timezone
from opal.models import Patient

from elcid.episode_categories import InfectionService
from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.admissions.models import Encounter, TransferHistory
from plugins.admissions import logger


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

# UPDATED_DATE is the same as CREATED_DATE if there
# has not been an update, ie its always set.
Q_GET_TRANSFERS_SINCE = """
    SELECT *
    FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE
    UPDATED_DATE >= @since
"""


def save_encounter(encounter, patient):
    """
    Given a dictionary of ENCOUNTER data from the upstream database,
    and the PATIENT for whom it concerns, save it.
    """
    our_encounter, created = Encounter.objects.get_or_create(
        patient=patient, upstream_id=encounter['ID']
    )

    if not created:
        logger.info('Updating existing encounter')

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

    our_encounter.save()
    logger.info('Saved encounter {}'.format(our_encounter.pk))

    return our_encounter, created


def load_encounters(patient):
    """
    Load any upstream admission data we may not have for PATIENT
    """
    api = ProdAPI()

    demographic     = patient.demographics()
    encounter_count = patient.encounters.count()

    encounters = api.execute_hospital_query(
        Q_GET_ALL_PATIENT_ENCOUNTERS,
        params={'mrn': demographic.hospital_number}
    )
    for encounter in encounters:
        save_encounter(encounter, patient)

    if encounter_count == 0:
        if patient.encounters.count() > 0:
            # We've stored the first encounter for this patient
            status = patient.patientencounterstatus_set.get()
            status.has_encounters = True
            status.save()


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
        mrn = encounter['PID_3_MRN'].strip()

        if mrn == '':
            continue

        if Demographics.objects.filter(hospital_number=mrn).exists():
            patient = Patient.objects.filter(demographics__hospital_number=mrn).first()
            save_encounter(encounter, patient)
        else:
            patient = create_rfh_patient_from_hospital_number(mrn, InfectionService)
            save_encounter(encounter, patient)
        patient.patientencounterstatus_set.update(
            has_encounters=True
        )


def load_transfer_history():
    """
    TEMP ONLY
    """
    api = ProdAPI()

    histories = api.execute_warehouse_query(
        Q_GET_ALL_HISTORY
    )
    for history in histories:

        try:
            hist = TransferHistory()
            for k, v in history.items():
                setattr(
                    hist,
                    TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                    v
                )
            hist.save()
        except:
            print(history)
            raise


def cast_to_transfer_history(upstream_dict):
    hist = TransferHistory()
    for k, v in upstream_dict.items():
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


@transaction.atomic
def create_transfer_histories_from_upstream_result(some_rows):
    slice_ids = [i["ENCNTR_SLICE_ID"] for i in some_rows]
    TransferHistory.objects.filter(
        encounter_slice_id__in=slice_ids
    ).delete()
    transfer_histories = []
    for some_row in some_rows:
        transfer_histories.append(
            cast_to_transfer_history(some_row)
        )
    TransferHistory.objects.bulk_create(transfer_histories)
    return transfer_histories
