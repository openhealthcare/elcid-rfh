"""
Unittests for the plugins.appointments.loader module
"""
from opal.core.test import OpalTestCase

from plugins.appointments.models import Appointment

from plugins.appointments import loader



class NonDateIdenticalTestCase(OpalTestCase):

    def test_identical(self):
        dict_one = {
            'appointment_id'  : '1234',
            'start_datetime'  : '2019-01-01 12:00:00'
        }
        dict_two = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': '2019-01-01 12:00:00'
        }
        appointment = Appointment(**dict_one)
        self.assertTrue(loader.non_date_identical(appointment, dict_two))


    def test_dates_different(self):
        dict_one = {
            'appointment_id'  : '1234',
            'start_datetime'  : '2019-01-01 12:00:00'
        }
        dict_two = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': '2009-02-01 12:00:00'
        }
        appointment = Appointment(**dict_one)
        self.assertTrue(loader.non_date_identical(appointment, dict_two))


    def test_non_dates_different(self):
        dict_one = {
            'appointment_id'  : '12',
            'start_datetime'  : '2019-01-01 12:00:00'
        }
        dict_two = {
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': '2019-01-01 12:00:00'
        }
        appointment = Appointment(**dict_one)
        self.assertFalse(loader.non_date_identical(appointment, dict_two))


class SaveOrDiscardTestCase(OpalTestCase):

    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        self.patient = p

    def test_save_appointment(self):
        appointment_data = {

        }
        pass


class LoadAppointmentTestCase(OpalTestCase):


    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        self.patient = p


    def test_load_apppointment(self):
        pass
