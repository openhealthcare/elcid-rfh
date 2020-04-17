import datetime
from rest_framework.reverse import reverse
from opal.core.test import OpalTestCase
from apps.tb import utils



class TestCleanObsNameTestCase(OpalTestCase):
    def test_with_ellipsis(self):
        r = utils.clean_observation_name("something...")
        self.assertEqual(r, "something")

    def test_without_ellipsis(self):
        r = utils.clean_observation_name("something")
        self.assertEqual(r, "something")


class TestCleanObsValueTestCase(OpalTestCase):
    def test_with_new_method(self):
        value = "8~Please note: New method effective 10/11/2015"
        r = utils.clean_observation_value(value)
        self.assertEqual(r, "8 Please note: New method effective 10/11/2015")

    def test_without_new_method(self):
        value = "8"
        r = utils.clean_observation_value(value)
        self.assertEqual(r, "8")

    def test_with_none(self):
        value = None
        r = utils.clean_observation_value(value)
        self.assertIsNone(r)
