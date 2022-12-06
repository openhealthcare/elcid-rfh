from opal.core.test import OpalTestCase
from plugins.imaging import models, loader

class UpdateImagingFromQueryResultTestCase(OpalTestCase):
	def test_update_patient_imaging_from_query_result(self):
		imaging_row = {
			k: None for k in models.Imaging.UPSTREAM_FIELDS_TO_MODEL_FIELDS.keys()
		}
		imaging_row["result_id"] = "789"
		imaging_row["patient_number"] = "123"
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(hospital_number="123")
		loader.update_imaging_from_query_result([imaging_row])
		self.assertEqual(
			patient.imaging.get().result_id, "789"
		)

	def test_update_merged_patient_imaging_from_query_result(self):
		imaging_row = {
			k: None for k in models.Imaging.UPSTREAM_FIELDS_TO_MODEL_FIELDS.keys()
		}
		imaging_row["result_id"] = "789"
		imaging_row["patient_number"] = "567"
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(hospital_number="123")
		patient.mergedmrn_set.create(
			mrn="567"
		)
		loader.update_imaging_from_query_result([imaging_row])
		self.assertEqual(
			patient.imaging.get().result_id, "789"
		)
