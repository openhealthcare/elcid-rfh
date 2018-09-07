import mock
import datetime
from opal.core.test import OpalTestCase
from intrahospital_api.apis.prod_api import ProdApi



class ProdApiTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        self.api = ProdApi()

    def test_demographics(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.demographics.return_value = "result"
            result = self.api.demographics_for_hospital_number("some_number")
            lab_tests.demographics.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")

    def test_lab_tests_for_hospital_number(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.lab_tests_for_hospital_number.return_value = "result"
            result = self.api.lab_tests_for_hospital_number("some_number")
            lab_tests.lab_tests_for_hospital_number.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")

    def test_lab_test_results_since(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.lab_test_results_since.return_value = "result"
            result = self.api.lab_test_results_since("some_number")
            lab_tests.lab_test_results_since.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")

    def test_raw_lab_tests(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.raw_lab_tests.return_value = "result"
            result = self.api.raw_lab_tests("some_number")
            lab_tests.raw_lab_tests.assert_called_once_with(
                "some_number", None, None
            )
            self.assertEqual(result, "result")

    def test_cooked_lab_tests(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.cooked_lab_tests.return_value = "result"
            result = self.api.cooked_lab_tests("some_number")
            lab_tests.cooked_lab_tests.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")
