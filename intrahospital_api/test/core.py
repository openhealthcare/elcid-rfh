from django.test import override_settings
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase


@override_settings(API_USER="ohc",  API_STATE="dev")
class ApiTestCase(OpalTestCase):
    def setUp(self):
        super(ApiTestCase, self).setUp()
        User.objects.create(username="ohc", password="fake_password")