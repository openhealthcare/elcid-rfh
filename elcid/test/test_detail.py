"""
Unittests for the elCID.detail module
"""
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from opal.models import UserProfile

from elcid import detail
from intrahospital_api import constants


class ResultTestCase(OpalTestCase):
    def setUp(self):
        self.permissioned = User.objects.create(
            username="permissioned", password="permissioned"
        )

        profile, _ = UserProfile.objects.get_or_create(
            user=self.permissioned
        )
        profile.roles.create(name=constants.VIEW_LAB_TESTS_IN_DETAIL)

        self.not_permissioned = User.objects.create(
            username="not_permissioned", password="not_permissioned"
        )
        UserProfile.objects.get_or_create(user=self.not_permissioned)

    def test_slug(self):
        self.assertEqual('test_results', detail.Result.get_slug())

    def test_visible_with_role(self):
        self.assertTrue(detail.Result.visible_to(self.permissioned))

    def test_invisible_without_role(self):
        self.assertFalse(
            detail.Result.visible_to(self.not_permissioned)
        )
