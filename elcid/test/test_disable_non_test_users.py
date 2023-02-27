from opal.core.test import OpalTestCase
from django.contrib.auth.models import User
from elcid.management.commands.disable_non_test_users import Command


class DisableNonTestUsersTestCase(OpalTestCase):
    def setUp(self):
        self.cmd = Command()

    def test_disables_users(self):
        User.objects.create(username='someone')
        self.cmd.handle()
        self.assertFalse(
            User.objects.get(username='someone').is_active
        )

    def test_except_certain_users(self):
        User.objects.create(username='ohc')
        self.cmd.handle()
        self.assertTrue(
            User.objects.get(username='ohc').is_active
        )
