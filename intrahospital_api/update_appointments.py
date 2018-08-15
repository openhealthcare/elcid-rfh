from opal.models import Patient
from elcid.models import Demographics
from intrahospital_api import get_api
from apps.tb.episode_categories import TbEpisode


def back_fill_appointments(patient):
    api = get_api()
    appointments = api.tb_appointments_for_hospital_number(
        patient.demographics_set.first().hospital_number
    )
    save_appointments(patient, appointments)


def save_appointments(patient, appointment_dicts):
    for appointment in appointment_dicts:
        # this should never happend
        if not appointment_exists(patient, appointment):
            patient.tbappointment_set.create(
                **appointment
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
        patient = Patient()
        patient.save()
        patient.demographics_set.update(
            hospital_number=hospital_number,
        )
        return patient, True


def get_or_create_episode(patient):
    episode = patient.episode_set.filter(
        category_name=TbEpisode.display_name
    )

    if episode:
        return episode, False
    else:
        episode = patient.episode_set.create(
            category_name=TbEpisode.display_name
        )
        return episode, True


def update_demographics(patient):
    hospital_number = patient.demographics_set.first().hospital_number
    api = get_api()
    demographics_dict = api.appoinments_api.demographics_for_hospital_number(
        hospital_number
    )
    patient.demographics_set.update(**demographics_dict)


def has_appointments(self, patient):
    return patient.tbappointment_set.exists()


def update_appointments():
    api = get_api()
    future_appointments = api.future_tb_appointments()
    for hospital_number, appointments in future_appointments.items():
        patient, patient_created = get_or_create_patient(hospital_number)
        episode, episode_created = get_or_create_episode(patient)
        if patient_created:
            update_demographics(patient)

        if episode_created:
            back_fill_appointments(patient)
        else:
            save_appointments(patient, appointments)
