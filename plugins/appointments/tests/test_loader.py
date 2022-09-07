"""
Unittests for the plugins.appointments.loader module
"""
from unittest import mock
import datetime

from django.utils import timezone
from opal.core.test import OpalTestCase

from plugins.appointments.models import Appointment

from plugins.appointments import loader


class SaveOrDiscardTestCase(OpalTestCase):

    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        self.patient = p

    def test_save_appointment(self):
        appointment_data = {
            'Appointment_ID':             '1234',
            'Appointment_Start_Datetime': datetime.datetime.now(),
        }
        loader.save_or_discard_appointment_data(appointment_data, self.patient)
        self.assertEqual('1234', self.patient.appointments.get().appointment_id)


    def test_save_updated_appointment(self):
        now = datetime.datetime.now()
        appointment_data = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : now,
            'HL7_Message_ID'            : '4567',
        }
        appointment_data_2 = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CANCELLED',
            'insert_date'               : now,
            'HL7_Message_ID'            : '4567',
        }
        loader.save_or_discard_appointment_data(appointment_data, self.patient)
        loader.save_or_discard_appointment_data(appointment_data_2, self.patient)
        self.assertEqual('CANCELLED', self.patient.appointments.get().status_code)



    def test_ignore_subsequent_appointment(self):
        now  = datetime.datetime.now()
        then = now - datetime.timedelta(days=2)
        appointment_data = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CANCELLED',
            'insert_date'               : now,
            'HL7_Message_ID'            : '4567',
        }
        appointment_data_2 = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : then,
            'HL7_Message_ID'            : '4567',
        }

        loader.save_or_discard_appointment_data(appointment_data, self.patient)
        loader.save_or_discard_appointment_data(appointment_data_2, self.patient)
        self.assertEqual('CANCELLED', self.patient.appointments.get().status_code)


    def test_ignore_duplicate_if_non_date_fields_identical(self):
        now  = datetime.datetime.now()
        then = now - datetime.timedelta(days=2)
        appointment_data = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : now,
            'HL7_Message_ID'            : '4567',
        }
        appointment_data_2 = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : then,
            'HL7_Message_ID'            : '4567',
        }

        loader.save_or_discard_appointment_data(appointment_data, self.patient)
        loader.save_or_discard_appointment_data(appointment_data_2, self.patient)
        self.assertEqual('CONFIRMED', self.patient.appointments.get().status_code)


class LoadAppointmentTestCase(OpalTestCase):


    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        self.patient = p

    def test_load_apppointment(self):
        now = datetime.datetime.now()
        appointment_data = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : now,
            'HL7_Message_ID'            : '4567',
        }

        with mock.patch.object(loader, 'ProdAPI') as mock_api:
            mock_api.return_value.execute_hospital_query.return_value = [appointment_data]

            loader.load_appointments(self.patient)


        self.assertEqual('CONFIRMED', self.patient.appointments.get().status_code)


    def test_load_apppointment_some_exist(self):
        now = datetime.datetime.now()
        then = now - datetime.timedelta(days=2)

        Appointment.objects.create(
            patient=self.patient,
            appointment_id='1234',
            insert_date=timezone.make_aware(then)
        )

        appointment_data = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : now,
            'HL7_Message_ID'            : '4567',
        }

        with mock.patch.object(loader, 'ProdAPI') as mock_api:
            mock_api.return_value.execute_hospital_query.return_value = [appointment_data]

            loader.load_appointments(self.patient)


        self.assertEqual('CONFIRMED', self.patient.appointments.get().status_code)
