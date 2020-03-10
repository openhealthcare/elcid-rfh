from unittest import mock
from collections import OrderedDict
from django.utils import timezone
from opal.core.test import OpalTestCase
from plugins.labtests import api as lab_test_api
from plugins.labtests import models


class RecentResultsApiTestCase(OpalTestCase):
    @mock.patch("plugins.labtests.api.json_response")
    def test_retrieve(self, json_response):
        patient, _ = self.new_patient_and_episode_please()
        api = lab_test_api.RecentResultsApiView()
        api.RELEVANT_TESTS = OrderedDict((("some_test_name", ["some_obs_name"]),))
        now = timezone.now()
        lab_test = patient.lab_tests.create(test_name="some_test_name")
        lab_test.observation_set.create(
            observation_name="some_obs_name",
            observation_datetime=now,
            observation_value="1",
        )
        api.retrieve(None, patient.id)
        json_response.assert_called_once_with(
            {"results": [{"name": "some_obs_name", "date": now, "result": "1",}]}
        )
