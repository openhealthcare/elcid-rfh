from django.contrib.auth.models import AnonymousUser, User

from opal.core.test import OpalTestCase
from opal.models import UserProfile

from elcid.context_processors import permissions


class PermissionsTestCase(OpalTestCase):
    def setUp(self):
        self.request = self.rf.get("/")

    def test_permissions_allowed(self):
        user = self.user
        UserProfile.objects.get_or_create(user=user)
        user.profile.roles.create(name="something")
        self.request.user = user
        self.assertEqual(
            permissions(self.request), dict(permissions=dict(something=True))
        )

    def test_permissions_inactive(self):
        user = User.objects.create(username="inactive", password="inactive")
        UserProfile.objects.get_or_create(user=user)
        user.profile.roles.create(name="something")
        user.is_active = False
        user.save()
        # make sure they haven't changed the name of the inactive property
        user = User.objects.get(username="inactive")
        self.request.user = user
        self.assertEqual(
            permissions(self.request), dict()
        )

    def test_permissions_anonymous(self):
        user = AnonymousUser()
        self.request.user = user
        self.assertEqual(
            permissions(self.request), dict()
        )
