from plugins.labtests import models
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import batch_load2
from unittest.mock import patch

ROOT = "intrahospital_api.management.commands.batch_load2"

class BatchLoad2TestCase(OpalTestCase):
	@patch(f"{ROOT}.get_count")
	@patch(f"{ROOT}.api")
	def test_handle(self, api, get_count):
		lab_fields = [
			i.name for i in models.LabTest._meta.get_fields() if i.name not in [
				"created_at", "updated_at"
			]
		]
		observation_fields = [
			i.name for i in models.Observation._meta.get_fields() if i.name not in [
				"created_at", "test_id"
			]
		]
		lab_test = {i: None for i in lab_fields}
		observations = [{i: None for i in observation_fields }]
		observations[0]["observation_name"] =  "Anti-CV2 (CRMP-5) antibodies"
		observations[0]["last_updated"] =  "01/03/2022 20:22:10"
		observations[0]["observation_datetime"] =  "01/03/2022 20:22:10"
		observations[0]["reported_datetime"] =  "01/03/2022 20:22:10"
		lab_test["test_name"] = "ANTI NEURONAL AB REFERRAL"
		lab_test["external_identifier"] = "234"
		lab_test["observations"] = observations
		query_result = [{
			"demographics": {
				"hospital_number": "123"
			},
			"lab_tests": [lab_test]
		}]
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(hospital_number="123")
		api.data_deltas.return_value = query_result
		get_count.return_value = 1
		batch_load2.Command().handle()
		self.assertTrue(
			patient.lab_tests.filter(lab_number="234").exists()
		)
