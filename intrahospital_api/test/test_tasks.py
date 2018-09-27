from mock import patch
from opal.core.test import OpalTestCase
from intrahospital_api import tasks


class LoadTestCase(OpalTestCase):
    @patch("intrahospital_api.loader.async_load_patient")
    def test_load(self, async_load_patient):
        async_load_patient.return_value = "some_result"
        result = tasks.load(1, 2)
        self.assertEqual(
            result, "some_result"
        )
        async_load_patient.assert_called_once_with(
            1, 2
        )
