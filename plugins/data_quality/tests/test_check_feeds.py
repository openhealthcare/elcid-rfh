from unittest import mock
import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from plugins.data_quality.checks import check_feeds


@mock.patch('plugins.data_quality.utils.send_email')
class CheckFeedsTestCase(OpalTestCase):
	def test_check_feeds_fail(self, send_email):
		first_of_jan_2021 = timezone.make_aware(datetime.datetime(
			2021, 1, 1
		))
		patient, _ = self.new_patient_and_episode_please()
		lab_test = patient.lab_tests.create()
		lab_test.observation_set.create(
			last_updated=first_of_jan_2021
		)
		patient.appointments.create(
			last_updated=first_of_jan_2021,
			insert_date=first_of_jan_2021
		)
		patient.imaging.create(
			date_reported=first_of_jan_2021
		)
		patient.masterfilemeta_set.create(
			last_updated=first_of_jan_2021
		)
		patient.encounters.create(
			last_updated=first_of_jan_2021
		)
		check_feeds.check_feeds()
		self.assertTrue(send_email.called)

	def test_check_feeds_succeed(self, send_email):
		an_hour_ago = timezone.now() - datetime.timedelta(hours=1)
		patient, _ = self.new_patient_and_episode_please()
		lab_test = patient.lab_tests.create()
		lab_test.observation_set.create(
			last_updated=an_hour_ago
		)
		patient.appointments.create(
			last_updated=an_hour_ago,
			insert_date=an_hour_ago
		)
		patient.imaging.create(
			date_reported=an_hour_ago
		)
		patient.masterfilemeta_set.create(
			last_updated=an_hour_ago
		)
		patient.encounters.create(
			last_updated=an_hour_ago
		)
		check_feeds.check_feeds()
		self.assertFalse(send_email.called)
