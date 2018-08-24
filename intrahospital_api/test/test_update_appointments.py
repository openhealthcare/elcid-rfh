import datetime
import mock
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api import update_appointments
from opal.models import Patient
from apps.tb import models as tb_models
from apps.tb.episode_categories import TbEpisode


@mock.patch("intrahospital_api.update_appointments.get_api")
class UpdateAllAppointmentsTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        _, self.tb_episode = self.new_patient_and_episode_please()
        _, self.other_episode = self.new_patient_and_episode_please()
        self.tb_episode.category_name = TbEpisode.display_name
        self.tb_episode.save()
        self.mock_api = mock.MagicMock()
        self.mock_api.user = self.user
        today = datetime.date.today()
        future = today + datetime.timedelta(1)
        past = today - datetime.timedelta(20)

        self.future_appointment = {
                'clinic_resource': u'RAL Davis, Dr David TB',
                'end': datetime.datetime(
                    future.year, future.month, future.day, 14, 10
                ),
                'location': u'RAL GROVE CLINIC',
                'start': datetime.datetime(
                    future.year, future.month, future.day, 14, 0
                ),
                'state': u'Confirmed'
        }

        self.past_appointment = {
            'clinic_resource': u'RAL Davis, Dr David TB',
            'end': datetime.datetime(
                past.year, past.month, past.day, 14, 10
            ),
            'location': u'RAL GROVE CLINIC',
            'start': datetime.datetime(
                past.year, past.month, past.day, 14, 0
            ),
            'state': u'Confirmed'
        }
        self.mock_api.tb_appointments_for_hospital_number.return_value = [
            self.future_appointment, self.past_appointment
        ]
        self.mock_api.user = self.user

        self.tb_episode.patient.tbappointment_set.create(
            state='Confirmed',
            start=self.past_appointment["start"],
            end=self.past_appointment["end"],
            location=self.past_appointment["location"],
            clinic_resource=self.past_appointment["clinic_resource"],
            created=self.past_appointment["start"] - datetime.timedelta(1),
            created_by=self.user
        )

    def test_update_all_appointments_existing(self, get_api):
        get_api.return_value = self.mock_api
        update_appointments.update_all_appointments()
        self.assertEqual(tb_models.TBAppointment.objects.count(), 2)
        self.assertEqual(self.tb_episode.patient.tbappointment_set.count(), 2)
        appointment_set = self.tb_episode.patient.tbappointment_set
        self.assertTrue(
            appointment_set.filter(**self.past_appointment).exists()
        )
        self.assertTrue(
            appointment_set.filter(**self.future_appointment).exists()
        )

    def test_update_all_appointments_new(self, get_api):
        tb_models.TBAppointment.objects.all().delete()
        get_api.return_value = self.mock_api
        update_appointments.update_all_appointments()
        self.assertEqual(tb_models.TBAppointment.objects.count(), 2)
        self.assertEqual(self.tb_episode.patient.tbappointment_set.count(), 2)
        appointment_set = self.tb_episode.patient.tbappointment_set
        self.assertTrue(
            appointment_set.filter(**self.past_appointment).exists()
        )
        self.assertTrue(
            appointment_set.filter(**self.future_appointment).exists()
        )


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
        api.user = self.user
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
        api.user = self.user
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
