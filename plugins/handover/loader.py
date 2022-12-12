"""
Load AMT Handovr records from upstream
"""
from django.db import transaction
from opal.models import Patient

from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from elcid.utils import find_patients_from_mrns
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.apis.prod_api import db_retry
from intrahospital_api.loader import create_rfh_patient_from_hospital_number

from plugins.icu import logger
from plugins.handover.models import AMTHandover, NursingHandover


Q_GET_AMT_HANDOVER = """
SELECT *
FROM
HandoverDB.View_Live_Acute_Medical_Team
WHERE
Discharged = 'Y'
"""

def get_upstream_data():
    """
    Fetch the upstream handover
    """
    api = ProdAPI()

    return api.execute_hospital_query(Q_GET_AMT_HANDOVER)


@transaction.atomic
def load_discharged_amt_handover():
    """
    Fetch upstream AMT patients who have been discharged

    This function is intended as a one time initial load.
    """
    results = get_upstream_data()

    AMTHandover.objects.filter(discharged='Y').delete()

    for result in results:

        mrn = result['MRN']

        if not Demographics.objects.filter(hospital_number=mrn).exists():
            create_rfh_patient_from_hospital_number(mrn, InfectionService)

            logger.info('Created patient for {}'.format(mrn))

        patient = Patient.objects.filter(demographics__hospital_number=mrn).first()

        handover = AMTHandover()

        handover.patient = patient

        for k, v in result.items():
            setattr(
                handover,
                AMTHandover.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                v
            )

        handover.save()

        amt_status = patient.patientamthandoverstatus_set.get()
        amt_status.has_handover = True
        amt_status.save()



Q_GET_CURRENT = """
SELECT *
FROM
HandoverDB.View_Live_Acute_Medical_Team
WHERE
Discharged = 'N'
"""

Q_GET_HANDOVER_BY_ID = """
SELECT *
FROM
HandoverDB.View_Live_Acute_Medical_Team
WHERE
id = @id
"""

def create_handover_from_upstream(patient, data):
    """
    Given an upstream data dictionary returned by the API,
    create a new AMTHandover record.
    """
    handover = AMTHandover()

    handover.patient = patient
    for k, v in data.items():
        setattr(
            handover,
            AMTHandover.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
            v
        )

    handover.save()
    return handover


@db_retry
def get_current():
    api = ProdAPI()
    return api.execute_hospital_query(Q_GET_CURRENT)


def sync_amt_handover():
    """
    The sync includes two operations:

    - Replace our local copy of the AMT handover for current patients
    - Update any that we think are current that have been discharged upstream

    This function is called from a management command + cron job
    """
    api = ProdAPI()
    current_patients = get_current()

    current_ids = [h['id'] for h in current_patients]

    mrns = [i["MRN"] for i in current_patients]
    mrn_to_patient = find_patients_from_mrns(mrns)
    for mrn in mrns:
        if mrn not in mrn_to_patient:
            mrn_to_patient[mrn] = create_rfh_patient_from_hospital_number(
                mrn, InfectionService
            )
            logger.info('Created patient for {}'.format(mrn))

    with transaction.atomic():
        for handover in current_patients:
            mrn = handover['MRN']

            if AMTHandover.objects.filter(sqlserver_id=handover['id']).exists():
                AMTHandover.objects.get(sqlserver_id=handover['id']).delete()

            handover_patient= mrn_to_patient.get(mrn)
            if not handover_patient:
                continue
            handover = create_handover_from_upstream(handover_patient, handover)

            amt_status = handover.patient.patientamthandoverstatus_set.get()
            if not amt_status.has_handover:
                amt_status.has_handover = True
                amt_status.save()

        discharged = AMTHandover.objects.exclude(
            sqlserver_id__in=current_ids
        ).filter(discharged='N')

        for handover in discharged:
            upstream = api.execute_hospital_query(
                Q_GET_HANDOVER_BY_ID, params={'id': handover.sqlserver_id})[0]

            handover.delete()
            create_handover_from_upstream(upstream)


Q_GET_ALL_NURSING_HANDOVER = """
SELECT *
FROM
VIEW_ElCid_Nursing_Handover
"""


def sync_nursing_handover():
    """
    Load patients from the upstream handover database
    """
    api = ProdAPI()

    previously_active = set(
        NursingHandover.objects.filter(
            active=True).values_list(
                'sqlserver_uniqueid', flat=True)
    )

    handovers = api.execute_hospital_query(Q_GET_ALL_NURSING_HANDOVER)
    mrns = set([i["Patient_MRN"] for i in handovers])
    mrn_to_patients = find_patients_from_mrns(mrns)
    for mrn in mrns:
        if mrn not in mrn_to_patients:
            our_mrn = mrn.lstrip('0')
            if our_mrn:
                logger.info('Created patient for {}'.format(our_mrn))
                mrn_to_patients[mrn] = create_rfh_patient_from_hospital_number(
                    our_mrn, InfectionService
                )

    with transaction.atomic():
        for handover in handovers:
            our_handover_patient = mrn_to_patients.get(handover["Patient_MRN"])
            if not our_handover_patient:
                continue

            sql_id = handover['SQLserver_UniqueID']

            our_handover, _ = NursingHandover.objects.get_or_create(
                sqlserver_uniqueid=sql_id,
                patient=our_handover_patient
            )

            for k, v in handover.items():
                setattr(
                    our_handover,
                    NursingHandover.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                    v
                )

            our_handover.save()

            previously_active.remove(sql_id)

            status = our_handover.patient.patientnursinghandoverstatus_set.get()

            if not status.has_handover:
                status.has_handover = True
                status.save()

        for sql_id in previously_active:
            handover = NursingHandover.objects.get(sqlserver_uniqueid=sql_id)
            handover.active = False
            handover.save()
