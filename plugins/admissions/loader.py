"""
Load admissions from upsteam
"""
import datetime
from collections import defaultdict

from django.db import transaction
from django.db.models import DateTimeField
from django.utils import timezone
from opal.models import Patient

from elcid.episode_categories import InfectionService
from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.admissions.models import Encounter, PatientEncounterStatus, TransferHistory, BedStatus
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
