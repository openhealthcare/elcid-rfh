"""
Loading Covid data from upstream
"""
from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number

from plugins.covid import lab, loader

Q_GET_COVID_IDS = """
SELECT DISTINCT Patient_Number FROM tQuest.Pathology_Result_view
WHERE OBR_exam_code_Text = @test_name
"""

def pre_load_covid_patients():
    """
    Fetch the set of patients who have had Covid 19 tests ordered.
    If any of these are not currently part of the elCID cohort,
    create these patients.
    """
    api = ProdAPI()

    patient_mrns = set()

    for test_name in lab.COVID_19_TEST_NAMES:

        results = api.execute_trust_query(
            Q_GET_COVID_IDS, params={'test_name': test_name})

        patient_mrns.update([r['Patient_Number'] for r in results])

    for mrn in patient_mrns:

        if Demographics.objects.filter(hospital_number=mrn).exists():
            continue

        create_rfh_patient_from_hospital_number(mrn, InfectionService)
