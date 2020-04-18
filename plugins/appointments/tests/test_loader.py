"""
Unittests for the plugins.appointments.loader module
"""
from opal.core.test import OpalTestCase

from plugins.appointments import loader


class NonDateIdenticalTestCase(OpalTestCase):

    def test_identical(self):
        dict_one = {
            'appointment_id'  : '1234',
            'appointment_date': '2019-01-01'
        }
        self.assertTrue(loader.non_date_identical(dict_one, dict_one))


    def test_dates_different(self):
        dict_one = {
            'appointment_id'  : '1234',
            'appointment_date': '2019-01-01'
        }
        dict_two = {
            'appointment_id'  : '1234',
            'appointment_date': '2017-08-09'
        }
        self.assertTrue(loader.non_date_identical(dict_one, dict_two))


    def test_non_dates_different(self):
        dict_one = {
            'appointment_id'  : '12',
            'appointment_date': '2019-01-01'
        }
        dict_two = {
            'appointment_id'  : '1234',
            'appointment_date': '2017-08-09'
        }
        self.assertFalse(loader.non_date_identical(dict_one, dict_two))


class SaveOrDiscardTestCase(OpalTestCase):

    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        self.patient = patient

    def test_save_appointment(self):
        appointment_data = {

        }
        pass


class LoadAppointmentTestCase(OpalTestCase):


    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        self.patient = patient


    def test_load_apppointment(self):
        pass
