from opal.core.test import OpalTestCase

from intrahospital_api.base_api import BaseApi


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

    def test_demographics_throws(self):
        self.method_test(
            "demographics", 'Please implement a demographics query'
        )

    def test_results(self):
        self.method_test(
            "results", 'Please implement a results query'
        )

    def test_raw_data(self):
        self.method_test(
            "raw_data",
            "Please a method that get's all raw data about a patient"
        )

    def test_cooked_data(self):
        self.method_test(
            "cooked_data",
            "Please a method that get's all cooked data about a patient"
        )
