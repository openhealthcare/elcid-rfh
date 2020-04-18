"""
Load Appointments from upstream
"""
import datetime

from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.appointments.models import Appointment
from plugins.appointments import logger


Q_GET_ALL_PATIENT_APPOINTMENTS = """
SELECT *
FROM VIEW_ElCid_CRS_OUTPATIENTS
WHERE vPatient_Number = @mrn
AND insert_date > @insert_date
"""


def non_date_identical(frist, second):
    """
    Predicate to determine whether two appointments are the same
    apart from date fields which weirdly often come in with added
    timezones

    Frist is an Appointment object
    Second is an upstream database dictionary
    """
    for k in second:
        if k.lower().find('date') == -1:
            if getattr(frist, Appointment.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]) != second[k]:
                return False
    return True


def save_or_discard_appointment_data(appointment, patient):
    """
    Given a dictionary of APPOINTMENT data from the upstream
    database, and the PATIENT for whom it concerns, decide
    whether to save or discard it, then do so.
    """
    appointment_id = appointment['Appointment_ID']
    # Find out if this appointment has been seen before
    if Appointment.objects.filter(appointment_id=appointment_id).exists():

        frist = Appointment.objects.get(appointment_id=appointment_id)

        if non_date_identical(frist, appointment):
            # If everything is the same, including the
            # HL7 message ID, don't worry about it.
            # In practice, these are upstream strptime formatting
            # weirdness that adds a timezone of +000
            msg = 'Discarding duplicate appointment data for {}'.format(
                appointment_id
            )
            logger.info(msg)
            return

        # otherwise there's a difference.
        # check which has the most recent insert date
        insert_date = datetime.datetime.strptime(
            appointment['insert_date'],
            '%Y-%m-%d %H:%M:%S'
        )
        if insert_date < frist.insert_date:
            msg = 'Discarding appointment data for {} with later insert_date than database'.format(
                appointment_id
            )
            logger.info(msg)
            return
        else:
            msg = 'Deleting previously stored data for {} as earlier version'.format(
                appointment_id
            )
            logger.info(msg)
            # The new one should replace the old one.
            frist.delete()

    our_appointment = Appointment(patient=patient)
    for k, v in appointment.items():
        setattr(
            our_appointment,
            Appointment.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v)

    our_appointment.save()
    logger.info('Saved appointment {}'.format(appointment_id))


def load_appointments(patient):
    """
    Load any upstream appointment data we may not have for PATIENT
    """
    api = ProdAPI()
    if patient.appointment_set.objects.count() > 0:
        insert_date = patient.appointment_set.objects.all().order_by('started').last().insert_date
    else:
        # Arbitrary, but the data suggests this is well before the actual lower bound
        insert_date = datetime.datetime(2010, 1, 1, 1, 1, 1)

    appointments = api.execute_hospital_query(
        Q_GET_ALL_PATIENT_APPOINTMENTS,
        params={'mrn': demographic.hospital_number, 'insert_date': insert_date}
    )

    for appointment in appointments:
        loader.save_or_discard_appointment_data(appointment)
