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
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 2,
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE",
				"MERGE_COMMENTS": "Merged"
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
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 2,
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 3,
				"PATIENT_NUMBER": "345",
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": "Merged"
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

	def test_ignores_active_patients_with_no_merge_comments(self, get_all_merged_patients, send_email):
		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": ""
			}
		]
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(
			hospital_number="123"
		)
		self.cmd.handle()
		self.assertFalse(send_email.called)

	def test_ignores_active_patients_with_null_merge_comments(self, get_all_merged_patients, send_email):
		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": None
			}
		]
		patient, _ = self.new_patient_and_episode_please()
		patient.demographics_set.update(
			hospital_number="123"
		)
		self.cmd.handle()
		self.assertFalse(send_email.called)

	def test_missing_inactive_patients(self, get_all_merged_patients, send_email):
		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 2,
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 3,
				"PATIENT_NUMBER": "345",
				"ACTIVE_INACTIVE": "INACTIVE",
				"MERGE_COMMENTS": "Merged"
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

	def test_active_patients_only_in_our_system(self, get_all_merged_patients, send_email):
		"""
		We have an active merged patient in our system that does not
		exist upstream.
		"""
		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 2,
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 3,
				"PATIENT_NUMBER": "345",
				"ACTIVE_INACTIVE": "INACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
		]
		patient_1, _ = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number="123"
		)
		patient_1.mergedmrn_set.create(
			mrn="234"
		)
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number="456"
		)
		patient_2.mergedmrn_set.create(
			mrn="345"
		)
		self.cmd.handle()
		send_email.assert_called_once_with(
			"We have 1 active MRN(s) that are not upstream"
		)


	def test_inactive_patients_only_in_our_system(self, get_all_merged_patients, send_email):
		"""
		We have an inactive merged patient in our system that does not
		exist upstream.
		"""
		get_all_merged_patients.return_value = [
			{
				"ID": 1,
				"PATIENT_NUMBER": "123",
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 2,
				"PATIENT_NUMBER": "234",
				"ACTIVE_INACTIVE": "INACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
			{
				"ID": 3,
				"PATIENT_NUMBER": "345",
				"ACTIVE_INACTIVE": "ACTIVE",
				"MERGE_COMMENTS": "Merged"
			},
		]
		patient_1, _ = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number="123"
		)
		patient_1.mergedmrn_set.create(
			mrn="234"
		)
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number="345"
		)
		patient_2.mergedmrn_set.create(
			mrn="456"
		)
		self.cmd.handle()
		send_email.assert_called_once_with(
			"We have 1 inactive MRN(s) that are not upstream"
		)
