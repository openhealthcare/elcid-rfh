import datetime
from django.utils import timezone
from django.urls import reverse
from opal.core.test import OpalTestCase
from plugins.appointments.models import Appointment
from plugins.tb import episode_categories, constants, models


class AppointmentListTestCase(OpalTestCase):
    def setUp(self):
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )
        self.url = reverse("tb_clinic_list")

    def test_context_data_today(self):
        patient, episode = self.new_patient_and_episode_please()
        demographics = patient.demographics()
        now = timezone.now()
        pcr = patient.lab_tests.create(
            test_name="TB PCR TEST"
        )
        pcr.observation_set.create(
            observation_name="TB PCR",
            observation_datetime=now - datetime.timedelta(4),
            observation_value="not used~",
            test=pcr
        )
        culture = patient.lab_tests.create(
            test_name="AFB : CULTURE"
        )
        culture.observation_set.create(
            observation_name="TB: Culture Result",
            observation_datetime=now - datetime.timedelta(3),
            observation_value="some value~",
            test=culture
        )
        episode.category_name = episode_categories.TbEpisode.display_name
        consultation = episode.patientconsultation_set.create(
            when=now,
            reason_for_interaction="Because",
            initials="MU"
        )
        episode.save()
        appointment = Appointment.objects.create(
            derived_appointment_type=constants.TB_APPOINTMENT_CODES[0],
            start_datetime=now,
            patient=patient
        )
        ctx = self.client.get(self.url).context
        self.assertEqual(len(ctx["rows_by_date"]), 1)
        dt, rows = list(ctx["rows_by_date"].items())[0]
        self.assertEqual(dt, now.date())
        not_canceled = rows['not_canceled']
        self.assertEqual(len(not_canceled), 1)
        row = not_canceled[0]

        self.assertEqual(
            row[0], appointment
        )
        self.assertEqual(
            row[1], demographics
        )
        self.assertEqual(
            row[2], episode
        )
        self.assertEqual(
            row[3], consultation
        )
        stats = rows['stats']
        self.assertEqual(stats, {'on_elcid': 1})

    def test_context_data_yesterday(self):
        patient, episode = self.new_patient_and_episode_please()
        episode.category_name = episode_categories.TbEpisode.display_name
        episode.save()
        Appointment.objects.create(
            derived_appointment_type=constants.TB_APPOINTMENT_CODES[0],
            start_datetime=timezone.now() - datetime.timedelta(1),
            patient=patient
        )
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["rows_by_date"], {})


class NurseLetterTestCase(OpalTestCase):
    def setUp(self):
        # create the property
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.patient_consultation = self.episode.patientconsultation_set.create(
            when=timezone.now()
        )
        self.url = reverse(
            "nurse_letter",
            kwargs={"pk": self.patient_consultation.id}
        )

    def test_get_bloods_with_breaks(self):
        when = timezone.now() - datetime.timedelta(1)
        lab_test = self.patient.lab_tests.create(
            test_name="LIVER PROFILE",
            datetime_ordered=when
        )
        obs = lab_test.observation_set.create(
            observation_name="ALT",
            observation_value="9",
            reference_range="10 - 50",
            observation_datetime=when
        )
        response = self.client.get(self.url)
        self.assertEqual(
            response.context["bloods"],
            [obs]
        )

    def test_get_bloods_without_breaks(self):
        when = timezone.now() - datetime.timedelta(1)
        lab_test = self.patient.lab_tests.create(
            test_name="LIVER PROFILE",
            datetime_ordered=when
        )
        obs = lab_test.observation_set.create(
            observation_name="ALT",
            observation_value="11",
            reference_range="10 - 50",
            observation_datetime=when
        )
        response = self.client.get(self.url)
        self.assertEqual(
            response.context["bloods"],
            [obs]
        )

    def test_get_bloods_no_bloods(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.context["bloods"],
            []
        )


class OnTBMedsTestCase(OpalTestCase):
    def test_get(self):
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123",
            first_name="Sarah",
            surname="Willis"
        )
        today = datetime.date.today()
        treatment = models.Treatment(
            episode=episode,
            category=models.Treatment.TB,
            start_date=today - datetime.timedelta(12)
        )
        treatment.drug = 'Bedaquiline'
        treatment.save()
        # create the property
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )
        url = reverse("on_tb_meds")
        self.client.login
        request = self.client.get(url)
        self.assertEqual(
            request.status_code, 200
        )
        ctx = request.context
        demographics, treatments = ctx["demographics_and_treatments"][0]
        self.assertEqual(demographics, patient.demographics())
        self.assertEqual(treatments, [treatment])
