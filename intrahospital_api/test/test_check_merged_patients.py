from unittest import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import check_merged_patients


@mock.patch('intrahospital_api.management.commands.check_merged_patients.logger')
@mock.patch('intrahospital_api.management.commands.check_merged_patients.get_all_merged_patients')
class CheckMergedPatientsTestCase(OpalTestCase):
	def setUp(self):
		self.cmd = check_merged_patients.Command()

	def test_no_issues(self, get_all_merged_patients, logger):
		"""
		There are no issues, we have a merged patient
		and an active patient
		"""

		get_all_merged_patients.return_value = [
			{
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE"
			},
			{
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE"
			},
		]
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(
			hospital_number="123"
		)
		patient.mergedmrn_set.create(
			mrn="234"
		)
		self.cmd.handle()
		self.assertFalse(logger.error.called)

	def test_missing_active_patients(self, get_all_merged_patients, logger):
		"""
		A patient with an INACTIVE MRN is attached to a wrong
		patient and we are missing the active MRN.
		"""
		get_all_merged_patients.return_value = [
			{
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE"
			},
			{
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE"
			},
		]
		patient_1, _ = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number="123"
		)
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number="345"
		)
		patient_2.mergedmrn_set.create(
			mrn="234"
		)
		self.cmd.handle()
		logger.error.assert_called_once_with(
			"We have 1 missing active MRN"
		)


	def test_missing_inactive_patients(self, get_all_merged_patients, logger):
		get_all_merged_patients.return_value = [
			{
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE"
			},
			{
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE"
			},
			{
				"PATIENT_NUMBER": "345",
				"ACTIVE_INACTIVE": "INACTIVE"
			},
		]
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(
			hospital_number="123"
		)
		patient.mergedmrn_set.create(
			mrn="234"
		)
		other_patient, _ = self.new_patient_and_episode_please()
		other_patient.demographics_set.update(
			hospital_number="345"
		)
		self.cmd.handle()
		logger.error.assert_called_once_with(
			"We have 1 missing inactive MRN"
		)
