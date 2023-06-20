import datetime

from django.utils import timezone
from rest_framework.reverse import reverse
from opal.core.test import OpalTestCase


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
        self.maxDiff = None
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
                }
            ]
        }
        self.assertEqual(result.json(), expected)


class TestTBTests(OpalTestCase):

    def setUp(self):
        self.request = self.rf.get("/")
        self.patient, _ = self.new_patient_and_episode_please()
        self.url = reverse(
            'tb_tests-detail',
            kwargs={"pk": self.patient.id},
            request=self.request
        )
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

    def test_no_TB_epispde(self):
        result = self.client.get(self.url)
        expected = {}
        self.assertEqual(result.json(), expected)
