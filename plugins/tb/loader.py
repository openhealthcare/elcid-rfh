import datetime
from django.utils import timezone
from django.db import transaction
from plugins.appointments import loader
from opal.models import Patient
from elcid.models import Demographics
from elcid import episode_categories as infection_episode_categories
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number
from plugins.tb import episode_categories, constants, logger, models


Q_TB_APPOINTMENTS = """
SELECT DISTINCT vPatient_Number FROM VIEW_ElCid_CRS_OUTPATIENTS
WHERE Derived_Appointment_Type = @appointment_type
AND insert_date > @since
"""

Q_TB_APPOINTMENTS_SINCE = """
SELECT * FROM VIEW_ElCid_CRS_OUTPATIENTS
WHERE Derived_Appointment_Type = @appointment_type
and Appointment_Start_Datetime > @since
"""

Q_TB_OBS_SINCE = """
SELECT distinct(Patient_Number) FROM tQuest.Pathology_Result_View
WHERE OBX_exam_code_Text = @obs_name AND OBR_exam_code_Text=@test_name
and date_inserted > @since
"""


@transaction.atomic
def create_patients_from_tb_tests():
    """
    For everyone who has a Smear, culture, ref lab report
    or TB PCR make sure we have a patient. We don't need to
    create TB episodes. This will be done by
    the TB observation cron job if they have
    resulted positive for TB
    """
    api = ProdAPI()
    three_days_ago = timezone.now() - datetime.timedelta(3)
    hns = set()
    for tb_obs_model in models.TB_OBS:
        for test_name in tb_obs_model.TEST_NAMES:
            query_result = api.execute_trust_query(
                Q_TB_OBS_SINCE, params={
                    "since": three_days_ago,
                    "test_name": test_name,
                    "obs_name": tb_obs_model.OBSERVATION_NAME
                }
            )
            hns = hns.union([i["Patient_Number"] for i in query_result])

    for hn in list(hns):
        # lab test MRNs can have preceding zeros, elCID does not use zero
        # prefixes as we match the upstream masterfile table
        hn = hn.lstrip('0')
        # don't process empty hospital numbers
        if not hn:
            continue
        if not Demographics.objects.filter(
            hospital_number=hn
        ).exists():
            create_rfh_patient_from_hospital_number(
                    hn, infection_episode_categories.InfectionService
            )


@transaction.atomic
def create_tb_episodes_for_appointments():
    """
    If a patient has a TB appointment coming up and they
    are not on elcid create them.

    If a patient has an upcoming TB appointment and no
    TB episode, create that.
    """
    api = ProdAPI()
    results = set()
    since = timezone.now() - datetime.timedelta(3)
    for appointment in constants.TB_APPOINTMENT_CODES:
        results_for_type = api.execute_hospital_query(
            Q_TB_APPOINTMENTS, params={
                'appointment_type': appointment,
                'since': since
            }
        )
        results.update(i["vPatient_Number"] for i in results_for_type)

    existing_hospital_numbers = set(Demographics.objects.filter(
        patient__episode__category_name=episode_categories.TbEpisode.display_name
    ).values_list("hospital_number", flat=True))
    created_patients = 0
    created_episodes = 0

    results = list(results)
    for mrn in results:
        if mrn not in existing_hospital_numbers:
            patient = Patient.objects.filter(
                demographics__hospital_number=mrn
            ).first()
            if not patient:
                created_patients += 1
                patient = create_rfh_patient_from_hospital_number(
                    mrn, infection_episode_categories.InfectionService
                )
            patient.create_episode(
                category_name=episode_categories.TbEpisode.display_name
            )
            created_episodes += 1

    logger.info(f"Created {created_patients} patients")
    logger.info(f"Created {created_episodes} episodes")


@transaction.atomic
def update_tb_patient(appointment_dict):
    mrn = appointment_dict["vPatient_Number"]
    if not mrn:
        return
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
        # new patients load in all appointments so we don't need
        # to check them again here
        return
    if not patient.episode_set.filter(
        category_name=episode_categories.TbEpisode.display_name
    ):
        patient.create_episode(
            category_name=episode_categories.TbEpisode.display_name
        )


def refresh_future_tb_appointments():
    api = ProdAPI()
    since = datetime.datetime.combine(
        datetime.date.today(), datetime.datetime.min.time()
    )
    for appointment_type in constants.TB_APPOINTMENT_CODES:
        result = api.execute_hospital_query(
            Q_TB_APPOINTMENTS_SINCE, params={
                'appointment_type': appointment_type,
                'since': since
            }
        )
        loader.update_appointments_from_query_result(result)
