import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from plugins.covid import extract


class GetClosestObservationTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        lt_1 = self.patient.lab_tests.create(test_name='test_name')
        self.obs_1 = lt_1.observation_set.create(
            observation_name='obs_name'
        )
        lt_2 = self.patient.lab_tests.create(test_name='test_name')
        self.obs_2 = lt_2.observation_set.create(
            observation_name='obs_name'
        )
        self.followup_date = datetime.date(2021, 11, 15)

    def test_no_obs(self):
        self.assertIsNone(
            extract.get_closest_observation(
                self.patient, 'test_name', 'obs_name', self.followup_date
            )
        )

    def test_multiple_later_dates(self):
        self.obs_1.observation_datetime = timezone.make_aware(
            datetime.datetime(2021, 11, 16)
        )
        self.obs_1.save()
        self.obs_2.observation_datetime = timezone.make_aware(
            datetime.datetime(2021, 11, 17)
        )
        self.obs_2.save()
        found_obs = extract.get_closest_observation(
            self.patient, 'test_name', 'obs_name', self.followup_date
        )
        self.assertEqual(found_obs.id, self.obs_1.id)

    def test_multiple_ealier_dates(self):
        self.obs_1.observation_datetime = timezone.make_aware(
            datetime.datetime(2021, 11, 13)
        )
        self.obs_1.save()
        self.obs_2.observation_datetime = timezone.make_aware(
            datetime.datetime(2021, 11, 14)
        )
        self.obs_2.save()
        found_obs = extract.get_closest_observation(
            self.patient, 'test_name', 'obs_name', self.followup_date
        )
        self.assertEqual(found_obs.id, self.obs_2.id)

    def test_later_date_vs_earlier_date(self):
        self.obs_1.observation_datetime = timezone.make_aware(
            datetime.datetime(2021, 11, 13)
        )
        self.obs_1.save()
        self.obs_2.observation_datetime = timezone.make_aware(
            datetime.datetime(2021, 11, 16)
        )
        self.obs_2.save()
        found_obs = extract.get_closest_observation(
            self.patient, 'test_name', 'obs_name', self.followup_date
        )
        self.assertEqual(found_obs.id, self.obs_2.id)

    def test_on_the_follow_up_date(self):
        self.obs_1.observation_datetime = timezone.make_aware(
            datetime.datetime(2021, 11, 15)
        )
        self.obs_1.save()
        found_obs = extract.get_closest_observation(
            self.patient, 'test_name', 'obs_name', self.followup_date
        )
        self.assertEqual(found_obs.id, self.obs_1.id)
