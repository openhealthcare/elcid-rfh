"""
Loading Covid data from upstream
"""
from opal.models import Patient
from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number
from plugins.appointments import loader as appointment_loader
from plugins.covid.episode_categories import CovidEpisode
from plugins.covid import constants

from plugins.covid import lab, loader

Q_GET_COVID_IDS = """
SELECT DISTINCT Patient_Number FROM tQuest.Pathology_Result_view
WHERE OBR_exam_code_Text = @test_name
"""

Q_COVID_APPOINTMENTS = """
SELECT DISTINCT vPatient_Number FROM VIEW_ElCid_CRS_OUTPATIENTS
WHERE Derived_Appointment_Type = @appointment_type
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



def create_followup_episodes():
    api = ProdAPI()
    results = set()
    for appointment in constants.COVID_FOLLOWUP_APPOINTMENT_TYPES:
        results_for_type = api.execute_hospital_query(
            Q_COVID_APPOINTMENTS, params={'appointment_type': appointment}
        )
        results.update(i["vPatient_Number"] for i in results_for_type)

    existing_hospital_numbers = set(Demographics.objects.filter(
        patient__episode__category_name=CovidEpisode.display_name
    ).values_list("hospital_number", flat=True))

    results = list(results)
    for mrn in results:
        if mrn not in existing_hospital_numbers:
            patient = Patient.objects.filter(
                demographics__hospital_number=mrn
            ).first()
            if not patient:
                patient = create_rfh_patient_from_hospital_number(mrn, InfectionService)

            patient.episode_set.create(
                category_name=CovidEpisode.display_name
            )
