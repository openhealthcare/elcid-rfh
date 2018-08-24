from opal.core.test import OpalTestCase

from intrahospital_api.apis.base_api import BaseApi


class BaseApiTestCase(OpalTestCase):
    def setUp(self):
        self.api = BaseApi()

    def method_test(self, some_method, some_exception_str):
        with self.assertRaises(NotImplementedError) as er:
            getattr(self.api, some_method)("some hospital_number")
        self.assertEqual(
            str(er.exception),
            some_exception_str
        )

    def test_demographics_for_hospital_number_throws(self):
        self.method_test(
            "demographics_for_hospital_number", 'Please implement a demographics query'
        )

    def test_lab_tests_for_hospital_number(self):
        self.method_test(
            "lab_tests_for_hospital_number", 'Please implement a lab tests query'
        )

    def test_raw_lab_tests(self):
        self.method_test(
            "raw_lab_tests",
            "Please a method that get's all raw data about a patient"
        )

    def test_cooked_lab_tests(self):
        self.method_test(
            "cooked_lab_tests",
            "Please a method that get's all cooked data about a patient"
        )
