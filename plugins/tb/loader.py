import datetime
from django.db import transaction
from plugins.appointments.models import PatientAppointmentStatus
from opal.models import Patient
from elcid.models import Demographics
from elcid import episode_categories as infection_episode_categories
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number
from plugins.tb import episode_categories, constants, logger
from plugins.appointments.loader import save_or_discard_appointment_data
from plugins.imaging.loader import load_imaging


Q_TB_APPOINTMENTS = """
SELECT DISTINCT vPatient_Number FROM VIEW_ElCid_CRS_OUTPATIENTS
WHERE Derived_Appointment_Type = @appointment_type
"""

Q_TB_APPOINTMENTS_SINCE = """
SELECT * FROM VIEW_ElCid_CRS_OUTPATIENTS
WHERE Derived_Appointment_Type = @appointment_type
and Appointment_Start_Datetime > @since
"""


@transaction.atomic
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
    load_imaging(patient)
    save_or_discard_appointment_data(appointment_dict, patient)


def refresh_future_tb_appointments():
    api = ProdAPI()
    since = datetime.datetime.combine(
        datetime.date.today(), datetime.datetime.min.time()
    )
    upstream_appointments = []
    for appointment_type in constants.TB_APPOINTMENT_CODES:
        result = api.execute_hospital_query(
            Q_TB_APPOINTMENTS_SINCE, params={
                'appointment_type': appointment_type,
                'since': since
            }
        )
        upstream_appointments.extend(result)

    updated_hns = []
    failed = 0

    for appointment in upstream_appointments:
        try:
            update_tb_patient(appointment)
        except Exception:
            failed += 1
        updated_hns.append(appointment["vPatient_Number"])

    PatientAppointmentStatus.objects.filter(
        patient__demographics__hospital_number__in=updated_hns
    ).update(
        has_appointments=True
    )
    logger.info(f"Updated {len(updated_hns)} patients appointments")
    if failed:
        logger.error(f"Failed to update {failed} appointments")
