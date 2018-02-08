import mock
import datetime
from opal.core.test import OpalTestCase
from intrahospital_api.apis import dev_api
from elcid import models as emodels
from lab import models as lmodels


class DevApiTestCase(OpalTestCase):
    def setUp(self):
        self.api = dev_api.DevApi()

    def test_get_date_of_birth(self):
        dob = self.api.get_date_of_birth()
        self.assertTrue(dob > datetime.date(1900, 1, 1))

    def test_demographics(self):
        demographics = self.api.demographics('some')
        expected_fields = [
            "sex",
            "date_of_birth",
            "first_name",
            "surname",
            "title",
            "nhs_number",
            "hospital_number",
            "external_system"
        ]
        self.assertEqual(
            demographics["external_system"], "DEV_API"
        )
        self.assertFalse(set(demographics.keys()) - set(expected_fields))
        for field in expected_fields:
            self.assertTrue(bool(demographics[field]))

    @mock.patch("intrahospital_api.apis.dev_api.random.choice")
    def test_demographics_male(self, choice):
        choice.side_effect = lambda x: x[0]
        demographics = self.api.demographics('some')
        self.assertEqual(demographics["sex"], "Male")
        self.assertIn(demographics["first_name"], dev_api.MALE_FIRST_NAMES)
        self.assertEqual(demographics["title"], "Dr")

    @mock.patch("intrahospital_api.apis.dev_api.random.choice")
    def test_demographics_female(self, choice):
        choice.side_effect = lambda x: x[1]
        demographics = self.api.demographics('some')
        self.assertEqual(demographics["sex"], "Female")
        self.assertIn(demographics["first_name"], dev_api.FEMALE_FIRST_NAMES)
        self.assertEqual(demographics["title"], "Ms")

    def test_results(self):
        with mock.patch.object(self.api, "create_lab_test"):
            self.api.results("123434223")
            self.assertEqual(
                self.api.create_lab_test.call_count,
                len(dev_api.TEST_BASES) * 10
            )

    def test_get_external_identifier(self):
        external_identifier = self.api.get_external_identifier()
        self.assertEqual(len(external_identifier), 9)

    def test_get_observation_value(self):
        some_val = self.api.get_observation_value("10 - 12")
        self.assertTrue(bool(some_val))
        self.assertTrue(isinstance(some_val, float))

    def test_cooked_data(self):
        cooked_data = self.api.cooked_data("q2343424")
        self.assertTrue(len(cooked_data) > 1)
        expected_fields = [
            'first_name',
            'surname',
            'title',
            'result_status',
            'observation_value',
            'sex',
            'hospital_number',
            'nhs_number',
            'date_of_birth',
            'test_name',
            'units',
            'external_system',
            'reference_range'
        ]
        self.assertEqual(
            set(expected_fields), set(cooked_data[0].keys())
        )

    def test_raw_data(self):
        self.assertEqual(len(self.api.raw_data("2323441312")), 1)
