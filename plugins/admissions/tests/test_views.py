from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from plugins.admissions import detail
from plugins.ipc import constants as ipc_constants

class LocationHistoryViewVisibilityTestCase(OpalTestCase):
	def setUp(self):
		self.view_user = User.objects.create(
			username="view_user"
		)

	def test_superuser(self):
		self.view_user.is_superuser = True
		self.assertTrue(detail.LocationHistoryView.visible_to(
			self.view_user
		))

	def test_ipc(self):
		self.view_user.profile.roles.create(
			name=ipc_constants.IPC_ROLE
		)
		self.assertTrue(detail.LocationHistoryView.visible_to(
			self.view_user
		))

	def test_other_user(self):
		self.assertFalse(detail.LocationHistoryView.visible_to(
			self.view_user
		))
