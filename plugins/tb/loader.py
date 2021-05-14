from opal.models import Patient
from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number
from plugins.tb import episode_categories, constants
from elcid import episode_categories as infection_episode_categories


Q_TB_APPOINTMENTS = """
SELECT DISTINCT vPatient_Number FROM VIEW_ElCid_CRS_OUTPATIENTS
WHERE Derived_Appointment_Type = @appointment_type
"""


def create_tb_episodes():
    api = ProdAPI()
    results = set()
    for appointment in constants.TB_APPOINTMENT_CODES:
        results_for_type = api.execute_hospital_query(
            Q_TB_APPOINTMENTS, params={'appointment_type': appointment}
        )
        results.update(i["vPatient_Number"] for i in results_for_type)

    existing_hospital_numbers = set(Demographics.objects.filter(
        patient__episode__category_name=episode_categories.TbEpisode.display_name
    ).values_list("hospital_number", flat=True))

    results = list(results)
    for mrn in results:
        if mrn not in existing_hospital_numbers:
            patient = Patient.objects.filter(
                demographics__hospital_number=mrn
            ).first()
            if not patient:
                patient = create_rfh_patient_from_hospital_number(
                    mrn, infection_episode_categories.InfectionService
                )
            patient.create_episode(
                category_name=episode_categories.TbEpisode.display_name
            )
