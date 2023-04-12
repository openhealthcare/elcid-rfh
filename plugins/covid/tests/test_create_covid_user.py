from unittest import mock
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from opal import models as opal_models
from plugins.covid.management.commands import create_covid_user

@mock.patch(
	'plugins.covid.management.commands.create_covid_user.send_mail'
)
class CreateCovidUserTestCase(OpalTestCase):
	def setUp(self):
		self.cmd = create_covid_user.Command()
		for role_name in ['view_lab_tests_in_list', 'view_lab_tests_in_detail', 'view_lab_test_trends', 'covid19']:
			opal_models.Role.objects.get_or_create(name=role_name)

	def test_creates_user(self, send_mail):
		self.cmd.handle(email="someone@nhs.net")
		user = User.objects.get(email="someone@nhs.net")
		self.assertEqual(user.first_name, "someone")
		self.assertEqual(user.username, "someone")
		self.assertTrue(user.profile.force_password_change)
		self.assertTrue(send_mail.called)
		self.assertEqual(
			set(user.profile.roles.values_list('name', flat=True)),
			set(['view_lab_tests_in_list', 'view_lab_tests_in_detail', 'view_lab_test_trends', 'covid19'])
		)

	def test_fails_on_duplicate_email(self, send_mail):
		User.objects.create(username="someone_else", email="someone@nhs.net")
		with self.assertRaises(ValueError):
			self.cmd.handle(email="someone@nhs.net")
		self.assertFalse(
			User.objects.exclude(username="someone_else").exists()
		)
		self.assertFalse(send_mail.called)
