import datetime

from django.utils import timezone
from rest_framework.reverse import reverse
from opal.core.test import OpalTestCase

from plugins.labtests import models

from plugins.tb import utils


class TestMultipleResults(OpalTestCase):
    LAB_TEST_DT   = timezone.make_aware(datetime.datetime(2019, 1, 4))
    OBS_DATE_TIME = timezone.make_aware(datetime.datetime(2019, 1, 5))

    TESTS_TO_OBS_TO_VALUES = {
        "C REACTIVE PROTEIN": [
            ("C Reactive Protein", 6.1, OBS_DATE_TIME),
        ],
        "LIVER PROFILE": [
            ("ALT", 29.1, OBS_DATE_TIME),
            ("AST", 38.9, OBS_DATE_TIME),
            ("Total Bilirubin", 37.0, OBS_DATE_TIME)
        ],
        "QUANTIFERON TB GOLD IT": [
            ("QFT IFN gamma result (TB1)", 0.0, OBS_DATE_TIME),
            ("QFT IFN gamme result (TB2)", 0.0, OBS_DATE_TIME),
            ("QFT TB interpretation", "INDETERMINATE", OBS_DATE_TIME),
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

    def create_lab_tests(self, lab_test_dt=None, tests_to_obs_values=None):
        if lab_test_dt is None:
            lab_test_dt = self.LAB_TEST_DT
        if tests_to_obs_values is None:
            tests_to_obs_values = self.TESTS_TO_OBS_TO_VALUES
        for test_name, obs in tests_to_obs_values.items():
            lab_test = self.patient.lab_tests.create(
                test_name=test_name,
                datetime_ordered=self.LAB_TEST_DT
            )
            for ob in obs:
                lab_test.observation_set.create(
                    observation_datetime=ob[2],
                    observation_name=ob[0],
                    observation_value=ob[1]
                )

    def test_get_lab_tests_none(self):
        result = self.client.get(self.url)
        self.assertEqual(result.json(), {"results": []})

    def test_get_lab_tests(self):
        self.create_lab_tests()
        result = self.client.get(self.url)
        expected = {
            'results': [
                {
                    'date': '05/01/2019 00:00:00',
                    'name': 'C Reactive Protein',
                    'result': '6.1'
                },
                {
                    'date': '05/01/2019 00:00:00',
                    'name': 'ALT',
                    'result': '29.1'
                },
                {
                    'date': '05/01/2019 00:00:00',
                    'name': 'AST',
                    'result': '38.9'
                },
                {
                    'date': '05/01/2019 00:00:00',
                    'name': 'Total Bilirubin',
                    'result': '37.0'
                },
                {
                    'date': '05/01/2019 00:00:00',
                    'name': 'QFT IFN gamma result (TB1)',
                    'result': '0.0'
                },
                {
                    'date': '05/01/2019 00:00:00',
                    'name': 'QFT IFN gamme result (TB2)',
                    'result': '0.0'
                },
                {
                    'date': '05/01/2019 00:00:00',
                    'name': 'QFT TB interpretation',
                    'result': 'INDETERMINATE'
                }
            ]
        }
        self.assertEqual(result.json(), expected)
