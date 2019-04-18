import datetime
from rest_framework.reverse import reverse
from opal.core.test import OpalTestCase
from apps.tb import utils
from plugins.labtests import models


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
        self.assertEqual(r, "8")

    def test_without_new_method(self):
        value = "8"
        r = utils.clean_observation_value(value)
        self.assertEqual(r, "8")


class TestMultipleResults(OpalTestCase):
    TESTS_TO_OBS_TO_VALUES = {
        "C REACTIVE PROTEIN": [
            ("C Reactive Protein", 6.1, ),
        ],
        "LIVER PROFILE": [
            ("ALT", 29.1),
            ("AST", 38.9),
            ("Total Bilirubin", 37.0)
        ],
        "QUANTIFERON TB GOLD IT": [
            ("QFT IFN gamma result (TB1)", 0.0),
            ("QFT IFN gamme result (TB2)", 0.0),
            ("QFT TB interpretation", "INDETERMINATE"),
        ]
    }

    def setUp(self):
        self.request = self.rf.get("/")
        self.patient, _ = self.new_patient_and_episode_please()
        self.url = reverse(
            'tb_test_summary-detail',
            kwargs={"pk": self.patient.id},
            request=self.request
        )
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

    def create_lab_tests(self, some_dt, tests_to_obs_values=None):
        if tests_to_obs_values is None:
            tests_to_obs_values = self.TESTS_TO_OBS_TO_VALUES
        for test_name, obs in tests_to_obs_values:
            lab_test = self.patient.lab_tests.create(
                test_name=test_name,
                datetime_ordered=some_dt
            )
            for ob in obs:
                lab_test.observation_set.create()

    def test_get_lab_tests_none(self):
        result = self.client.get(self.url)
        self.assertEqual(result.json(), {"results": []})
