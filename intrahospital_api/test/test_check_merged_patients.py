from unittest import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import check_merged_patients


@mock.patch('intrahospital_api.management.commands.check_merged_patients.send_email')
@mock.patch('intrahospital_api.management.commands.check_merged_patients.get_all_merged_patients')
class CheckMergedPatientsTestCase(OpalTestCase):
	def setUp(self):
		self.cmd = check_merged_patients.Command()

	def test_no_issues(self, get_all_merged_patients, send_email):
		"""
		There are no issues, we have a merged patient
		and an active patient
		"""

		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE"
			},
			{
				"ID": 2,
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
		self.assertFalse(send_email.called)

	def test_intersection(self, get_all_merged_patients, send_email):
		"""
		We have created a MergedMRN with the same MRN as a hospital number
		"""
		patient_1, _ = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number="123"
		)
		patient_1.mergedmrn_set.create(
			mrn="234"
		)
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number="234"
		)
		self.cmd.handle()
		send_email.assert_called_once_with(
			"1 MRN(s) are in the MergedMRN table AND Demographics"
		)


	def test_missing_active_patients(self, get_all_merged_patients, send_email):
		"""
		A patient with an INACTIVE MRN is attached to a wrong
		patient and we are missing the active MRN.
		"""
		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE"
			},
			{
				"ID": 2,
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
		send_email.assert_called_once_with(
			"We have 1 missing active MRN(s)"
		)


	def test_missing_inactive_patients(self, get_all_merged_patients, send_email):
		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE"
			},
			{
				"ID": 2,
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE"
			},
			{
				"ID": 3,
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
		send_email.assert_called_once_with(
			"We have 1 missing inactive MRN(s)"
		)
