"""
Load AMT Handovr records from upstream
"""
from django.db import transaction
from opal.models import Patient

from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
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

def create_handover_from_upstream(data):
    """
    Given an upstream data dictionary returned by the API,
    create a new AMTHandover record.
    """
    handover = AMTHandover()

    handover.patient = Patient.objects.filter(
        demographics__hospital_number=data['MRN']).first()

    for k, v in data.items():
        setattr(
            handover,
            AMTHandover.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
            v
        )

    handover.save()
    return handover


@transaction.atomic
def sync_amt_handover():
    """
    The sync includes two operations:

    - Replace our local copy of the AMT handover for current patients
    - Update any that we think are current that have been discharged upstream

    This function is called from a management command + cron job
    """
    api = ProdAPI()

    current_patients = api.execute_hospital_query(Q_GET_CURRENT)

    current_ids = [h['id'] for h in current_patients]

    for handover in current_patients:

        mrn = handover['MRN']

        if AMTHandover.objects.filter(sqlserver_id=handover['id']).exists():
            AMTHandover.objects.get(sqlserver_id=handover['id']).delete()

        if not Demographics.objects.filter(hospital_number=mrn).exists():
            create_rfh_patient_from_hospital_number(mrn, InfectionService)

            logger.info('Created patient for {}'.format(mrn))

        handover = create_handover_from_upstream(handover)

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


@transaction.atomic
def sync_nursing_handover():
    """
    Load patients from the upstream handover database
    """
    api = ProdAPI()

    handovers = api.execute_hospital_query(Q_GET_ALL_NURSING_HANDOVER)

    for handover in handovers:

        mrn = handover['Patient_MRN']

        if NursingHandover.objects.filter(
                sqlserver_uniqueid=handover['SQLserver_UniqueID']
        ).exists():
            NursingHandover.objects.get(
                sqlserver_uniqueid=handover['SQLserver_UniqueID']
            ).delete()

        if not Demographics.objects.filter(hospital_number=mrn).exists():
            create_rfh_patient_from_hospital_number(mrn, InfectionService)

            logger.info('Created patient for {}'.format(mrn))

        our_handover = NursingHandover()

        our_handover.patient = Patient.objects.filter(
            demographics__hospital_number=mrn
        ).first()

        for k, v in handover.items():
            setattr(
                our_handover,
                NursingHandover.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                v
            )

        our_handover.save()

        status = our_handover.patient.patientnursinghandoverstatus_set.get()

        if not status.has_handover:
            status.has_handover = True
            status.save()
