import mock
from opal.core.test import OpalTestCase
from intrahospital_api.apis.prod_api import ProdApi


class ProdApiTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        self.api = ProdApi()

    def test_demographics(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.demographics.return_value = "result"
            result = self.api.demographics("some_number")
            lab_tests.demographics.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")

    def test_results_for_hospital_number(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.results_for_hospital_number.return_value = "result"
            result = self.api.results_for_hospital_number("some_number")
            lab_tests.results_for_hospital_number.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")

    def test_data_deltas(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.data_deltas.return_value = "result"
            result = self.api.data_deltas("some_number")
            lab_tests.data_deltas.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")

    def test_raw_data(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.raw_data.return_value = "result"
            result = self.api.raw_data("some_number")
            lab_tests.raw_data.assert_called_once_with(
                "some_number", None, None
            )
            self.assertEqual(result, "result")

    def test_cooked_data(self):
        with mock.patch.object(self.api, "lab_test_api") as lab_tests:
            lab_tests.cooked_data.return_value = "result"
            result = self.api.cooked_data("some_number")
            lab_tests.cooked_data.assert_called_once_with(
                "some_number"
            )
            self.assertEqual(result, "result")
