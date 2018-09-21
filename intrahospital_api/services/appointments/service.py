from django.utils import timezone
from opal.models import Patient
from elcid.models import Demographics
from intrahospital_api.base import service_utils
from intrahospital_api.constants import EXTERNAL_SYSTEM
from apps.tb.episode_categories import TbEpisode
from apps.tb.patient_lists import TbPatientList


def back_fill_appointments(patient):
    api = service_utils.get_api("appointments")
    appointments = api.tb_appointments_for_hospital_number(
        patient.demographics_set.first().hospital_number
    )
    save_appointments(patient, appointments)


def save_appointments(patient, appointment_dicts):
    api = service_utils.get_api("appointments")
    user = service_utils.get_user()
    created = timezone.now()
    created_by = user
    for appointment in appointment_dicts:
        if not appointment_exists(patient, appointment):
            patient.tbappointment_set.create(
                created=created, created_by=created_by, **appointment
            )


def appointment_exists(patient, appointment_dict):
    return patient.tbappointment_set.filter(
        start=appointment_dict["start"],
    ).exists()


def get_or_create_patient(hospital_number):
    demographics = Demographics.objects.filter(
        hospital_number=hospital_number
    ).first()

    if demographics:
        return demographics.patient, False
    else:
        api = service_utils.get_api("appointments")
        patient = Patient()
        patient.save()
        patient.demographics_set.update(
            hospital_number=hospital_number,
            external_system=EXTERNAL_SYSTEM,
            created=timezone.now(),
            created_by=api.user
        )
        return patient, True


def get_or_create_episode(patient):
    api = service_utils.get_api("appointments")
    user = service_utils.get_user()
    episode = patient.episode_set.filter(
        category_name=TbEpisode.display_name
    )

    if episode:
        return episode, False
    else:
        episode = patient.episode_set.create(
            category_name=TbEpisode.display_name,
            stage="New Referral"
        )
        episode.set_tag_names([TbPatientList.tag], user)
        return episode, True


def update_demographics(patient):
    hospital_number = patient.demographics_set.first().hospital_number
    service_utils.get_api('appointments')
    appoinments_api = service_utils.get_api("appointments")
    demographics_dict = appoinments_api.demographics_for_hospital_number(
        hospital_number
    )
    patient.demographics_set.update(**demographics_dict)


def has_appointments(patient):
    return patient.tbappointment_set.exists()


def update_all_appointments():
    appoinments_api = service_utils.get_api("appointments")
    appointments = appoinments_api.appointments_since_last_year()
    patient_ids = []
    for hospital_number, appointments in appointments.items():
        patient, _ = get_or_create_patient(hospital_number)
        get_or_create_episode(patient)
        back_fill_appointments(patient)
        patient_ids.append(patient.id)
    patients = Patient.objects.filter(
        episode__category_name="TB"
    ).exclude(id__in=patient_ids)

    for patient in patients:
        back_fill_appointments(patient)


def update_appointments():
    api = service_utils.get_api("appointments")
    future_appointments = api.future_tb_appointments()
    for hospital_number, appointments in future_appointments.items():
        patient, patient_created = get_or_create_patient(hospital_number)
        _, episode_created = get_or_create_episode(patient)
        if patient_created:
            update_demographics(patient)

        if episode_created:
            back_fill_appointments(patient)
        else:
            save_appointments(patient, appointments)
