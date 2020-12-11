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

        patient = Patient.objects.get(demographics__hospital_number=mrn)

        handover, _ = AMTHandover.objects.get_or_create(patient=patient)

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
