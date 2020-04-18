"""
Unittests for the plugins.appointments.models module
"""
from opal.core.test import OpalTestCase

from plugins.appointments import models


class AppointmentTestCase(OpalTestCase):

    def setUp(self):
        patient, episode = self.new_patient_and_episode_please()
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

    def test_to_dict(self):
        appointment = models.Appointment.objects.first()
        dicted = appointment.to_dict()
        self.assertEqual('TB', dicted['derived_appointment_type'])
        self.assertEqual('Dr Spock', dicted['derived_clinic_resource'])
        for k in models.Appointment.FIELDS_TO_SERIALIZE:
            self.assertTrue(k in dicted)

    def test_to_upstream_dict(self):
        appointment = models.Appointment.objects.first()
        dicted = appointment.to_upstream_dict()
        self.assertEqual('12345', dicted['HL7_Message_ID'])
        self.assertEqual('Dr Dre', dicted['vReferring_Doctor_Name'])
