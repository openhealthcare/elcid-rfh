from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from elcid.models import Diagnosis
from plugins.tb import epr

class GetDefaultConsultationTestCase(OpalTestCase):
	def setUp(self):
		_, self.episode = self.new_patient_and_episode_please()
		self.doctor = User.objects.create(
			first_name="Sarah",
			last_name="Watson",
			email="s.watson@nhs.net",
			username="s.watson"
		)
		self.pc = self.episode.patientconsultation_set.create(
			created_by=self.doctor
		)


	def test_with_primary_diagnosis(self):
		self.pc.plan = "Continue to monitor in clinic"
		expected = "".join([
			"\n\n** Plan **\n\n",
			"Continue to monitor in clinic\n\n",
			"** Written by **\n\n",
			"Sarah Watson s.watson@nhs.net s.watson\n\n",
			"END OF NOTE\n\n"
		])
		found = epr.get_default_consultation(self.pc)
		self.assertEqual(expected, found)


	def test_without_primary_diagnosis(self):
		self.pc.plan = "Continue to monitor in clinic"
		primary_diagnosis = self.pc.episode.diagnosis_set.create(
			category=Diagnosis.PRIMARY,
		)
		primary_diagnosis.condition = "Respiratory TB"
		primary_diagnosis.save()
		expected = "".join([
			"\n\n** Diagnosis **\n\n",
			"Respiratory TB"
			"\n** Plan **\n\n",
			"Continue to monitor in clinic\n\n",
			"** Written by **\n\n",
			"Sarah Watson s.watson@nhs.net s.watson\n\n",
			"END OF NOTE\n\n"
		])
		found = epr.get_default_consultation(self.pc)
		self.assertEqual(expected, found)
