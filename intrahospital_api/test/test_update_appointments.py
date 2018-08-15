import datetime
import mock
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api import update_appointments
from opal.models import Patient
from apps.tb.episode_categories import TbEpisode


@mock.patch("intrahospital_api.update_appointments.get_api")
class UpdateAppointmentsTestCase(OpalTestCase):

    def test_update_appointments(self, get_api):
        api = get_api.return_value
        appointments = [{
            'clinic_resource': u'RAL Davis, Dr David TB',
            'end': datetime.datetime(2018, 9, 18, 14, 10),
            'location': u'RAL GROVE CLINIC',
            'start': datetime.datetime(2018, 9, 18, 14, 0),
            'state': u'Confirmed'
        }]

        api.tb_appointments_for_hospital_number.return_value = appointments
        api.future_tb_appointments.return_value = {
            "11111": appointments
        }
        api.appoinments_api.demographics_for_hospital_number.return_value = dict(
            hospital_number="11111",
            first_name="Wilma",
            surname="Flintstone",
            date_of_birth=datetime.date(1000, 1, 1)
        )
        update_appointments.update_appointments()
        patient = Patient.objects.get(demographics__hospital_number="11111")
        demographics = patient.demographics_set.first()
        self.assertEqual(
            demographics.first_name, "Wilma"
        )
        self.assertEqual(
            demographics.surname, "Flintstone"
        )
        self.assertEqual(
            demographics.date_of_birth, datetime.date(1000, 1, 1)
        )
        appointment = patient.tbappointment_set.get()
        self.assertEqual(
            appointment.start, timezone.make_aware(
                datetime.datetime(2018, 9, 18, 14, 0)
            )
        )
        episode = patient.episode_set.get()
        self.assertEqual(
            episode.category_name, TbEpisode.display_name
        )

    def test_patient_exists(self, get_api):
        patient = Patient.objects.create()
        patient.demographics_set.update(
            hospital_number="11111",
            first_name="Betty",
            surname="Rubble",
            date_of_birth=datetime.date(2000, 1, 1)
        )
        api = get_api.return_value
        appointments = [{
            'clinic_resource': u'RAL Davis, Dr David TB',
            'end': datetime.datetime(2018, 9, 18, 14, 10),
            'location': u'RAL GROVE CLINIC',
            'start': datetime.datetime(2018, 9, 18, 14, 0),
            'state': u'Confirmed'
        }]

        api.tb_appointments_for_hospital_number.return_value = appointments
        api.future_tb_appointments.return_value = {
            "11111": appointments
        }
        api.appoinments_api.demographics_for_hospital_number.return_value = dict(
            hospital_number="11111",
            first_name="Wilma",
            surname="Flintstone",
            date_of_birth=datetime.date(1000, 1, 1)
        )
        update_appointments.update_appointments()
        patient = Patient.objects.get(demographics__hospital_number="11111")
        demographics = patient.demographics_set.first()
        self.assertEqual(
            demographics.first_name, "Betty"
        )
        self.assertEqual(
            demographics.surname, "Rubble"
        )
        self.assertEqual(
            demographics.date_of_birth, datetime.date(2000, 1, 1)
        )
        appointment = patient.tbappointment_set.get()
        self.assertEqual(
            appointment.start, timezone.make_aware(
                datetime.datetime(2018, 9, 18, 14, 0)
            )
        )
        episode = patient.episode_set.get()
        self.assertEqual(
            episode.category_name, TbEpisode.display_name
        )
