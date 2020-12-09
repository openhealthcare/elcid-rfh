import datetime
from django.utils import timezone
from django.urls import reverse
from opal.core.test import OpalTestCase
from plugins.appointments.models import Appointment
from plugins.tb import episode_categories, views, constants


class AppointmentListTestCase(OpalTestCase):
    def setUp(self):
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )
        self.url = reverse("tb_appointment_list")

    def test_context_data_today(self):
        patient, episode = self.new_patient_and_episode_please()
        episode.category_name = episode_categories.TbEpisode.display_name
        episode.save()
        appointment = Appointment.objects.create(
            derived_appointment_type=constants.TB_APPOINTMENT_CODES[0],
            start_datetime=timezone.now(),
            patient=patient
        )
        ctx = self.client.get(self.url).context
        ctx["admission_and_episode"] = [(appointment, episode,)]

    def test_context_data_yesterday(self):
        patient, episode = self.new_patient_and_episode_please()
        episode.category_name = episode_categories.TbEpisode.display_name
        episode.save()
        appointment = Appointment.objects.create(
            derived_appointment_type=constants.TB_APPOINTMENT_CODES[0],
            start_datetime=timezone.now() - datetime.timedelta(1),
            patient=patient
        )
        ctx = self.client.get(self.url).context
        ctx["admission_and_episode"] = []



