import datetime

from django.utils import timezone
from rest_framework.reverse import reverse
from opal.core.test import OpalTestCase

from plugins.labtests import models

from plugins.tb import api, episode_categories


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


class TBCalendarTestCase(OpalTestCase):
    def setUp(self):
        self.api = api.TBCalendar()
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.episode.category_name = episode_categories.TbEpisode.display_name
        self.episode.save()

    def test_get_mdt_date(self):
        # A wednesday
        mdt_dt = datetime.date(2021, 8, 18)
        self.assertEqual(
            self.api.get_mdt_date(mdt_dt),
            mdt_dt
        )

        # A Monday
        self.assertEqual(
            self.api.get_mdt_date(
                datetime.date(2021, 8, 16)
            ),
            mdt_dt
        )

        # A Friday
        self.assertEqual(
            self.api.get_mdt_date(
                datetime.date(2021, 8, 13)
            ),
            mdt_dt
        )

    def test_get_last_discussed(self):
        now = timezone.now()
        pc = self.episode.patientconsultation_set.create()
        pc.reason_for_interaction = "MDT meeting"
        pc.created = now
        pc.save()
        self.assertEqual(
            self.api.get_last_discussed(self.patient),
            now
        )

    def get_get_last_discussed_none(self):
        self.assertEqual(
            self.api.get_last_discussed(self.patient),
            api.MDT_START
        )

    def test_get_added_to_mdt_today_after_mdt(self):
        now = timezone.now()
        self.episode.addtomdt_set.create(
            when=datetime.date.today()
        )
        self.assertEqual(
            list(self.api.get_added_to_mdts(self.patient, now)), []
        )

    def test_get_get_added_to_mdt_today_before_mdt(self):
        now = timezone.now()
        yesterday = now - datetime.timedelta(1)
        mdt = self.episode.addtomdt_set.create(
            when=datetime.date.today()
        )
        self.assertEqual(
            list(self.api.get_added_to_mdts(self.patient, yesterday)),
            [mdt]
        )

    def test_get_positive_obs_discussed(self):
        now = timezone.now()
        yesterday = now - datetime.timedelta(1)
        yesterday_morning = yesterday - datetime.timedelta(hours=1)
        self.patient.tbpcr_set.create(
            reported_datetime=yesterday_morning,
            pending=False,
            positive=True
        )
        today_pcr = self.patient.tbpcr_set.create(
            reported_datetime=now,
            pending=False,
            positive=True
        )
        now = timezone.now()
        self.assertEqual(
            self.api.get_positive_tb_obs(self.patient, yesterday),
            [today_pcr]
        )
