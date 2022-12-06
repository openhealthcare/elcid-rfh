"""
Unittests for the plugins.appointments.loader module
"""
from unittest import mock
import datetime

from django.utils import timezone
from opal.core.test import OpalTestCase

from plugins.appointments.models import Appointment

from plugins.appointments import loader


class LoadAppointmentTestCase(OpalTestCase):
    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        p.demographics_set.update(
            hospital_number="2345"
        )
        self.patient = p

    def test_load_appointment(self):
        now = datetime.datetime.now()
        appointment_data = {
            'vPatient_Number'           : '2345',
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : now,
            'last_updated'              : None,
            'HL7_Message_ID'            : '4567',
        }

        with mock.patch.object(loader, 'ProdAPI') as mock_api:
            mock_api.return_value.execute_hospital_query.return_value = [appointment_data]
            loader.load_appointments(self.patient)
        self.assertEqual('CONFIRMED', self.patient.appointments.get().status_code)


    @mock.patch('plugins.appointments.loader.get_changed_appointment_fields')
    def test_load_appointment_some_exist(self, get_changed_appointment_fields):
        now = datetime.datetime.now()
        then = now - datetime.timedelta(days=2)

        # get changed appointments is there for logging purposes only
        # and requires a full dictionary of upstream appointment data
        # so lets return an empty dictionary
        get_changed_appointment_fields.return_value = {}

        Appointment.objects.create(
            patient=self.patient,
            appointment_id='1234',
            insert_date=timezone.make_aware(then)
        )

        appointment_data = {
            'vPatient_NHS_Number'       : None,
            'vPatient_Number'           : '2345',
            'Appointment_ID'            : '1234',
            'Appointment_Start_Datetime': now,
            'Appointment_Status_Code'   : 'CONFIRMED',
            'insert_date'               : now,
            'last_updated'              : now,
            'HL7_Message_ID'            : '4567',
        }

        with mock.patch.object(loader, 'ProdAPI') as mock_api:
            mock_api.return_value.execute_hospital_query.return_value = [appointment_data]

            loader.load_appointments(self.patient)


        self.assertEqual('CONFIRMED', self.patient.appointments.get().status_code)
