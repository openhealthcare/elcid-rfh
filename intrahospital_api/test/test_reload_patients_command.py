from opal.core.test import OpalTestCase
from elcid import episode_categories as infection_episode_categories
from intrahospital_api.management.commands import reload_patients
from unittest import mock

@mock.patch(
	'intrahospital_api.management.commands.reload_patients.loader.load_patient'
)
@mock.patch(
	'intrahospital_api.management.commands.reload_patients.loader.create_rfh_patient_from_hospital_number'
)
class ReloadPatientsTestCase(OpalTestCase):
	def setUp(self):
		self.cmd = reload_patients.Command()

	def test_reloads_a_patient(self, create_rfh_patient_from_hospital_number, load_patient):
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(hospital_number="123")
		with mock.patch.object(self.cmd.stdout, "write") as writer:
			self.cmd.handle(mrns=["123"])
		load_patient.assert_called_once_with(patient, run_async=False)
		self.assertFalse(create_rfh_patient_from_hospital_number.called)
		writer.assert_called_once_with("Looking at 123, 1/1")
