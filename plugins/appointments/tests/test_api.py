"""
Unittests for the plugins.appointments.api module
"""
from unittest import mock

from opal.core.test import OpalTestCase

from plugins.appointments import models

from plugins.appointments import api


class AppointmentViewSetTestCase(OpalTestCase):

    def setUp(self):
        patient, episode = self.new_patient_and_episode_please()
        self.patient=patient
        models.Appointment.objects.create(
            patient=patient,
            v_referring_doctor_name='Dr Dre',
            v_attending_doctor_name='Dr Jekyll',
            duration='10',
            status_code='CONFIRMED',
            derived_appointment_type='TB',
            derived_appointment_location='Grove',
            derived_appointment_location_site='RAL',
            derived_clinic_resource='Dr Spock',
            hl7_message_id='12345',
            appointment_id='231156.000'
        )
        models.Appointment.objects.create(
            patient=patient,
            v_referring_doctor_name='Dr Dre',
            v_attending_doctor_name='Dr Jekyll',
            duration='10',
            status_code='CONFIRMED',
            derived_appointment_type='TB FOLLOW UP',
            derived_appointment_location='Grove',
            derived_appointment_location_site='RAL',
            derived_clinic_resource='Dr Spock',
            hl7_message_id='12346',
            appointment_id='231157.000'
        )

    def test_retrieve(self):
        viewset  = api.AppointmentViewSet()

        response = viewset.retrieve(mock.MagicMock(), self.patient.pk)

        self.assertEqual(200, response.status_code)
        self.assertEqual('TB FOLLOW UP', response.data[1]['derived_appointment_type'])
        self.assertEqual('TB', response.data[0]['derived_appointment_type'])
