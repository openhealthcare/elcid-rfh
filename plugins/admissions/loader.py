"""
Load admissions from upsteam
"""
import datetime

from django.db.models import DateTimeField
from django.utils import timezone
from opal.models import Patient

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


def load_recent_encounters():
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

    timestamp = datetime.datetime.now() - datetime.timedelta(days=1)

    encounters = api.execute_hospital_query(
        Q_GET_RECENT_ENCOUNTERS,
        params={'timestamp': timestamp}
    )
    for encounter in encounters:
        mrn = encounter['PID_3_MRN']

        if Demographics.objects.filter(hospital_number=mrn).exists():
            patient = Patient.objects.filter(demographics__hospital_number=mrn).first()

            save_encounter(encounter, patient)


def load_transfer_history():
    """
    TEMP ONLY
    """
    api = ProdAPI()

    histories = api.execute_hospital_query(
        Q_GET_ALL_HISTORY
    )
    for history in histories:

        hist = TransferHistory()
        for k, v in history.items():
            setattr(
                hist,
                TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                v
            )
        hist.save()
