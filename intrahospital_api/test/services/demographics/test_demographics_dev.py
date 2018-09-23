import datetime
import mock
from opal.core.test import OpalTestCase
from intrahospital_api.services.demographics.backends import dev
from opal.core import serialization


class DevApiTestCase(OpalTestCase):
    def setUp(self):
        self.api = dev.Api()

    def test_get_date_of_birth(self):
        dob_str = self.api.get_date_of_birth()
        dob = serialization.deserialize_date(dob_str)
        self.assertTrue(dob > datetime.date(1900, 1, 1))

    def test_demographics(self):
        demographics = self.api.demographics_for_hospital_number('some')
        expected_fields = [
            "sex",
            "date_of_birth",
            "ethnicity",
            "first_name",
            "surname",
            "title",
            "nhs_number",
            "hospital_number",
            "external_system"
        ]
        self.assertEqual(
            demographics["external_system"], "RFH Database"
        )
        self.assertFalse(set(demographics.keys()) - set(expected_fields))
        for field in expected_fields:
            self.assertTrue(bool(demographics[field]))

    @mock.patch("intrahospital_api.services.demographics.backends.dev.random.choice")
    def test_demographics_male(self, choice):
        choice.side_effect = lambda x: x[0]
        demographics = self.api.demographics_for_hospital_number('some')
        self.assertEqual(demographics["sex"], "Male")
        self.assertIn(demographics["first_name"], dev.MALE_FIRST_NAMES)
        self.assertEqual(demographics["title"], "Dr")

    @mock.patch("intrahospital_api.services.demographics.backends.dev.random.choice")
    def test_demographics_female(self, choice):
        choice.side_effect = lambda x: x[1]
        demographics = self.api.demographics_for_hospital_number('some')
        self.assertEqual(demographics["sex"], "Female")
        self.assertIn(demographics["first_name"], dev.FEMALE_FIRST_NAMES)
        self.assertEqual(demographics["title"], "Ms")

    def test_get_external_identifier(self):
        external_identifier = self.api.get_external_identifier()
        self.assertEqual(len(external_identifier), 9)