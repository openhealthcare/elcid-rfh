import datetime
from collections import OrderedDict
from django.utils import timezone
from opal.core.test import OpalTestCase
from plugins.labtests import utils


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


class RecentObservationsTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.now = timezone.now()
        self.yesterday = self.now - datetime.timedelta(1)

    def test_ignores_pending(self):
        lab_test_1 = self.patient.lab_tests.create(test_name="some_test_name")
        lab_test_1.observation_set.create(
            observation_name="some_obs_name",
            observation_value="Pending",
            observation_datetime=self.now,
        )
        lab_test_2 = self.patient.lab_tests.create(test_name="some_test_name")
        lab_test_2.observation_set.create(
            observation_name="some_obs_name",
            observation_value="1",
            observation_datetime=self.yesterday,
        )
        test_names_to_obs_names = OrderedDict((("some_test_name", ["some_obs_name"]),))
        self.assertEqual(
            dict(utils.recent_observations(self.patient, test_names_to_obs_names)),
            {
                "some_obs_name": {
                    "observation_datetime": self.yesterday,
                    "observation_value": "1",
                }
            },
        )

    def test_does_not_ignore_pending(self):
        """
        Should not ignore pending if its the only result
        """
        lab_test = self.patient.lab_tests.create(test_name="some_test_name")
        lab_test.observation_set.create(
            observation_name="some_obs_name",
            observation_value="Pending",
            observation_datetime=self.now,
        )
        test_names_to_obs_names = OrderedDict((("some_test_name", ["some_obs_name"]),))
        self.assertEqual(
            dict(utils.recent_observations(self.patient, test_names_to_obs_names)),
            {
                "some_obs_name": {
                    "observation_datetime": self.now,
                    "observation_value": "Pending",
                }
            },
        )

    def test_gets_recent(self):
        lab_test_1 = self.patient.lab_tests.create(test_name="some_test_name")
        lab_test_1.observation_set.create(
            observation_name="some_obs_name",
            observation_value="2",
            observation_datetime=self.now,
        )
        lab_test_2 = self.patient.lab_tests.create(test_name="some_test_name")
        lab_test_2.observation_set.create(
            observation_name="some_obs_name",
            observation_value="1",
            observation_datetime=self.yesterday,
        )
        test_names_to_obs_names = OrderedDict((("some_test_name", ["some_obs_name"]),))
        self.assertEqual(
            dict(utils.recent_observations(self.patient, test_names_to_obs_names)),
            {
                "some_obs_name": {
                    "observation_datetime": self.now,
                    "observation_value": "2",
                }
            },
        )

    def test_only_brings_in_stated_lab_tests(self):
        lab_test_1 = self.patient.lab_tests.create(test_name="some_other_test_name")
        lab_test_1.observation_set.create(
            observation_name="some_obs_name",
            observation_value="2",
            observation_datetime=self.now,
        )
        test_names_to_obs_names = OrderedDict((("some_test_name", ["some_obs_name"]),))
        self.assertEqual(
            dict(utils.recent_observations(self.patient, test_names_to_obs_names)), {}
        )

    def test_only_brings_in_stated_observations(self):
        lab_test_1 = self.patient.lab_tests.create(test_name="some_test_name")
        lab_test_1.observation_set.create(
            observation_name="some_other_obs_name",
            observation_value="2",
            observation_datetime=self.now,
        )
        test_names_to_obs_names = OrderedDict((("some_test_name", ["some_obs_name"]),))
        self.assertEqual(
            dict(utils.recent_observations(self.patient, test_names_to_obs_names)), {}
        )

    def test_correctly_orders_lab_tests(self):
        lab_test_1 = self.patient.lab_tests.create(test_name="some_test_name_2")
        lab_test_1.observation_set.create(
            observation_name="some_obs_name_2",
            observation_value="2",
            observation_datetime=self.now,
        )
        lab_test_2 = self.patient.lab_tests.create(test_name="some_test_name_3")
        lab_test_2.observation_set.create(
            observation_name="some_obs_name_3",
            observation_value="3",
            observation_datetime=self.yesterday,
        )
        lab_test_3 = self.patient.lab_tests.create(test_name="some_test_name_1")
        lab_test_3.observation_set.create(
            observation_name="some_obs_name_1",
            observation_value="1",
            observation_datetime=self.now,
        )
        test_names_to_obs_names = OrderedDict(
            (
                ("some_test_name_1", ["some_obs_name_1"]),
                ("some_test_name_2", ["some_obs_name_2"]),
                ("some_test_name_3", ["some_obs_name_3"]),
            )
        )
        expected = OrderedDict()
        expected["some_obs_name_1"] = {
            "observation_value": "1",
            "observation_datetime": self.now,
        }

        expected["some_obs_name_2"] = {
            "observation_value": "2",
            "observation_datetime": self.now,
        }

        expected["some_obs_name_3"] = {
            "observation_value": "3",
            "observation_datetime": self.yesterday,
        }
        self.assertEqual(
            expected, utils.recent_observations(self.patient, test_names_to_obs_names)
        )

    def test_correctly_orders_observations(self):
        lab_test_1 = self.patient.lab_tests.create(test_name="some_test_name_1")
        lab_test_1.observation_set.create(
            observation_name="some_obs_name_2",
            observation_value="2",
            observation_datetime=self.now,
        )

        lab_test_1.observation_set.create(
            observation_name="some_obs_name_3",
            observation_value="3",
            observation_datetime=self.now,
        )
        lab_test_1.observation_set.create(
            observation_name="some_obs_name_1",
            observation_value="1",
            observation_datetime=self.yesterday,
        )
        test_names_to_obs_names = OrderedDict(
            (
                (
                    "some_test_name_1",
                    ["some_obs_name_1", "some_obs_name_2", "some_obs_name_3"],
                ),
            )
        )
        expected = OrderedDict()
        expected["some_obs_name_1"] = {
            "observation_value": "1",
            "observation_datetime": self.yesterday,
        }

        expected["some_obs_name_2"] = {
            "observation_value": "2",
            "observation_datetime": self.now,
        }

        expected["some_obs_name_3"] = {
            "observation_value": "3",
            "observation_datetime": self.now,
        }
        self.assertEqual(
            expected, utils.recent_observations(self.patient, test_names_to_obs_names)
        )
