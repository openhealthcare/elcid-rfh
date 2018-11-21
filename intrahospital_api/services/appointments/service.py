"""
Appointments service for elCID RFH
"""
import datetime
from opal.models import Patient
from opal.core import serialization
from elcid import models as elcid_models
from apps.tb.episode_categories import TbEpisode
from intrahospital_api.services.base import service_utils, db
from intrahospital_api.services.base import load_utils
from apps.tb.episode_categories import TbEpisode
from apps.tb.patient_lists import TbPatientList


def _get_or_create_appointment(patient, appointment_dict):
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY
    """
    start = serialization.deserialize_datetime(
            appointment_dict["start"]
    )
    appointment = patient.appointment_set.filter(
        start=start
    ).first()

    if appointment:
        return appointment, False
    else:
        return elcid_models.Appointment(patient=patient), True


def _has_changed(appointment, appointment_dict):
    """
    Returns True if an appointment has changed

    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY
    """
    for key in appointment_dict.keys():
        model_value = getattr(appointment, key)
        if isinstance(model_value, datetime.datetime):
            model_value = db.to_datetime_str(model_value)
        elif isinstance(model_value, datetime.date):
            model_value = db.to_date_str(model_value)

        if not model_value == appointment_dict[key]:
            return True
    return False


def _save_appointments(patient, appointment_dicts):
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY
    """
    user = service_utils.get_user()
    count = 0
    for appointment_dict in appointment_dicts:
        appointment, is_new = _get_or_create_appointment(
            patient, appointment_dict
        )
        if is_new or _has_changed(appointment, appointment_dict):
            appointment.update_from_api_dict(appointment_dict, user)
            count += 1
    return count


def _load_patient(patient):
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY
    """
    api = service_utils.get_backend("appointments")
    appointments = api.tb_appointments_for_hospital_number(
        patient.demographics_set.first().hospital_number
    )
    return _save_appointments(patient, appointments)


def refresh_patient(patient):
    """
    PUBLIC FUNCTION, CALLED EXTERNALLY
    """
    if patient.episode_set.filter(
        category_name=TbEpisode.display_name
    ).exists():
        patient.appointment_set.all().delete()
        _load_patient(patient)


def _load_patients():
    """
    INTERNAL FUNCTION, NEVER CALLED EXTERNALLY

    Loads in all appointments for all patients with the category of tb
    """
    patients = Patient.objects.filter(
        episode__category_name=TbEpisode.display_name
    )
    updated = 0

    for patient in patients:
        loaded = _load_patient(patient)
        if loaded:
            updated += loaded

    return updated


# not an invalid, name, its not a constant, seperate out
# for testing purposes
# pylint: disable=invalid-name
batch_load = load_utils.batch_load(
    service_name="appointments"
)(
    _load_patients
)
