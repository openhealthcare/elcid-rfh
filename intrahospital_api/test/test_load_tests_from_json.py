import json
import mock
import datetime
from django.test import override_settings
from django.utils import timezone
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import load_tests_from_json
from elcid import models as emodels

example_json = """
[{
"status": "complete",
"external_identifier": "123423137",
"site": "^& ^",
"test_code": "b12_and_folate_screen",
"test_name": "B12 AND FOLATE SCREEN",
"clinical_info": "testing",
"external_system": "RFH Database",
"datetime_ordered": "19/07/2018 15:04:22",
"observations": [
{
"units": "ng/L",
"observation_datetime": "20/07/2018 12:01:23",
"observation_name": "Vitamin B12",
"observation_number": "12015325",
"last_updated": "19/07/2018 14:44:22",
"observation_value": "89.7",
"reference_range": "160 - 925"
},
{
"units": "ng/L",
"observation_datetime": "20/07/2018 12:01:23",
"observation_name": "Folate",
"observation_number": "12015326",
"last_updated": "20/07/2018 11:42:12",
"observation_value": "-2.7",
"reference_range": "3.9 - 26.8"
}]
}]
""".strip()


@mock.patch(
    "intrahospital_api.management.commands.load_tests_from_json.json.load"
)
@override_settings(API_USER="api_user")
class LoadTestsFromJson(OpalTestCase):
    def setUp(self):
        # initialise the test user
        User.objects.create(username="api_user")

    def test_loads_in_tests(self, json_load):
        command = load_tests_from_json.Command()
        test_results = json.loads(example_json)
        patient, _ = self.new_patient_and_episode_please()
        command.process(patient, test_results)
        self.assertEqual(
            patient.lab_tests.count(), 1
        )
        lab_test = patient.lab_tests.get()
        self.assertEqual(
            lab_test.test_code, "b12_and_folate_screen"
        )
        expected_ordered = datetime.datetime(2018, 7, 19, 15, 4, 22)
        self.assertEqual(
            timezone.make_naive(lab_test.datetime_ordered),
            expected_ordered
        )

    def test_deletes_existing_tests(self, json_load):
        command = load_tests_from_json.Command()
        patient, _ = self.new_patient_and_episode_please()
        patient.lab_tests.create()
        command.process(patient, [])
        self.assertFalse(patient.lab_tests.exists())
