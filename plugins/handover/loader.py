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
from plugins.handover.models import AMTHandover


Q_GET_AMT_HANDOVER = """
SELECT *
FROM
HandoverDB.View_Live_Acute_Medical_Team
WHERE
Date_Referral_Added >= 2020-01-01
"""

def get_upstream_data():
    """
    Fetch the upstream handover
    """
    api = ProdAPI()

    return api.execute_hospital_query(Q_GET_AMT_HANDOVER)


@transaction.atomic
def load_amt_handover():
    """
    Fetch upstream AMT this year
    """
    results = get_upstream_data()

    AMTHandover.objects.all().delete()

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
            Q_GET_HANDOVER_BY_ID, id=handover.sqlserver_id)[0]

        handover.delete()
        create_handover_from_upstream(upstream)
