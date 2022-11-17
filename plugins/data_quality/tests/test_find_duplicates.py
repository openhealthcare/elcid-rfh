from unittest import mock
from opal.core.test import OpalTestCase
from plugins.data_quality.checks import find_duplicates


@mock.patch('plugins.data_quality.utils.send_email')
class FindExactDuplicatesTestCase(OpalTestCase):
	def test_finds_exact_cleanable_duplicates(self, send_email):
		"""
		Cleanable duplicates are when we can delete one without issue.

		In this case only patient 1 has a subrecord so
		patient 2 can be deleted.
		"""
		patient_1, episode = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number='111111',
		)
		diagnosis = episode.diagnosis_set.create()
		diagnosis.condition = "Cough"
		diagnosis.save()
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number='111111',
		)
		find_duplicates.find_exact_duplicates()
		call_args = send_email.call_args[0]
		self.assertEqual(
			call_args[0], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["title"], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["uncleanable_duplicates"], []
		)
		self.assertEqual(
			call_args[2]["cleanable_duplicates"], [(patient_2, patient_1,)]
		)
		self.assertEqual(
			call_args[2]["uncleanable_duplicates"], []
		)

	def test_finds_exact_uncleanable_duplicates(self, send_email):
		"""
		Cleanable duplicates are when we can delete one without issue.

		In this case only patient 1 has a subrecord so
		patient 2 can be deleted.
		"""
		patient_1, episode_1 = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number='111111',
		)
		diagnosis = episode_1.diagnosis_set.create()
		diagnosis.condition = "Cough"
		diagnosis.save()
		patient_2, episode_2 = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number='111111',
		)
		diagnosis = episode_2.diagnosis_set.create()
		diagnosis.condition = "Fever"
		diagnosis.save()
		find_duplicates.find_exact_duplicates()
		call_args = send_email.call_args[0]
		self.assertEqual(
			call_args[0], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["title"], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["cleanable_duplicates"], []
		)
		self.assertEqual(
			call_args[2]["uncleanable_duplicates"], [(patient_1, patient_2,)]
		)

	def test_does_not_find_exact_duplicates(self, send_email):
		patient_1, _ = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number='111111',
		)
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number='22222222',
		)
		find_duplicates.find_exact_duplicates()
		self.assertFalse(send_email.called)


@mock.patch('plugins.data_quality.utils.send_email')
class FindLeadingZeroDuplicatesTestCase(OpalTestCase):
	def test_finds_leading_zero_cleanable_duplicates(self, send_email):
		"""
		Cleanable duplicates are when we can delete one without issue.

		In this case only patient 1 has a subrecord so
		patient 2 can be deleted.
		"""
		patient_1, episode = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number='111111',
		)
		diagnosis = episode.diagnosis_set.create()
		diagnosis.condition = "Cough"
		diagnosis.save()
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number='0111111',
		)
		find_duplicates.find_zero_leading_duplicates()
		call_args = send_email.call_args[0]
		self.assertEqual(
			call_args[0], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["title"], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["uncleanable_duplicates"], []
		)
		self.assertEqual(
			call_args[2]["cleanable_duplicates"], [(patient_2, patient_1,)]
		)
		self.assertEqual(
			call_args[2]["uncleanable_duplicates"], []
		)

	def test_finds_leading_zero_uncleanable_duplicates(self, send_email):
		"""
		Cleanable duplicates are when we can delete one without issue.

		In this case only patient 1 has a subrecord so
		patient 2 can be deleted.
		"""
		patient_1, episode_1 = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number='111111',
		)
		diagnosis = episode_1.diagnosis_set.create()
		diagnosis.condition = "Cough"
		diagnosis.save()
		patient_2, episode_2 = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number='0111111',
		)
		diagnosis = episode_2.diagnosis_set.create()
		diagnosis.condition = "Fever"
		diagnosis.save()
		find_duplicates.find_zero_leading_duplicates()
		call_args = send_email.call_args[0]
		self.assertEqual(
			call_args[0], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["title"], '1 Exact hospital number duplicates'
		)
		self.assertEqual(
			call_args[2]["cleanable_duplicates"], []
		)
		self.assertEqual(
			call_args[2]["uncleanable_duplicates"], [(patient_2,patient_1,)]
		)

	def test_does_not_find_leading_zero_duplicates(self, send_email):
		patient_1, _ = self.new_patient_and_episode_please()
		patient_1.demographics_set.update(
			hospital_number='111111',
		)
		patient_2, _ = self.new_patient_and_episode_please()
		patient_2.demographics_set.update(
			hospital_number='022222222',
		)
		find_duplicates.find_zero_leading_duplicates()
		self.assertFalse(send_email.called)
