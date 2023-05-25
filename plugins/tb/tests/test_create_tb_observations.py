from django.utils import timezone
import datetime
from opal.core.test import OpalTestCase
from plugins.tb.management.commands import create_tb_observations
from plugins.tb import models as tb_models
from plugins.tb import episode_categories

class PopulateTestsTestCase(OpalTestCase):
	def setUp(self):
		self.patient, _ = self.new_patient_and_episode_please()
		self.now = timezone.now()
		self.yesterday = self.now - datetime.timedelta(1)

	def test_creates_afb_smear(self):
		lt = self.patient.lab_tests.create(
			test_name='AFB : CULTURE',
			lab_number="123",
			site="chest",
		)
		lt.observation_set.create(
			observation_datetime=self.yesterday,
			reported_datetime=self.now,
			observation_value='AAFB + Seen.',
			observation_name='AFB Smear'
		)
		create_tb_observations.populate_tests()
		afb_smear = tb_models.AFBSmear.objects.get()
		self.assertTrue(afb_smear.positive)


	def test_creates_afb_culture(self):
		lt = self.patient.lab_tests.create(
			test_name='AFB : CULTURE',
			lab_number="123",
			site="chest",
		)
		lt.observation_set.create(
			observation_datetime=self.yesterday,
			reported_datetime=self.now,
			observation_value='1) Mycobacterium sp.~  Isolate sent to Reference Laboratory~~~',
			observation_name='TB: Culture Result'
		)
		create_tb_observations.populate_tests()
		afb_culture = tb_models.AFBCulture.objects.get()
		self.assertTrue(afb_culture.positive)


	def test_creates_afb_ref_lab(self):
		lt = self.patient.lab_tests.create(
			test_name='AFB : CULTURE',
			lab_number="123",
			site="chest",
		)
		lt.observation_set.create(
			observation_datetime=self.yesterday,
			reported_datetime=self.now,
			observation_value="1) Mycobacterium tuberculosis~  This is a final reference laboratory report~~                        1)~  Ethambutol            S~  Isoniazid             S~  Pyrazinamide          S~  Rifampicin            S~~",
			observation_name='TB Ref. Lab. Culture result'
		)
		create_tb_observations.populate_tests()
		afb_ref_lab = tb_models.AFBRefLab.objects.get()
		self.assertTrue(afb_ref_lab.positive)

	def test_creates_pcr(self):
		lt = self.patient.lab_tests.create(
			test_name='TB PCR TEST',
			lab_number="123",
			site="chest",
		)
		lt.observation_set.create(
			observation_datetime=self.yesterday,
			reported_datetime=self.now,
			observation_value="The PCR to detect M.tuberculosis complex was~POSITIVE",
			observation_name='TB PCR'
		)
		create_tb_observations.populate_tests()
		tb_pcr = tb_models.TBPCR.objects.get()
		self.assertTrue(tb_pcr.positive)

class CMDTestCase(OpalTestCase):
	def setUp(self):
		self.patient, _ = self.new_patient_and_episode_please()
		self.cmd = create_tb_observations.Command()

	def create_positive_tb_test(self):
		now = timezone.now()
		yesterday = now - datetime.timedelta(1)

		lt = self.patient.lab_tests.create(
			test_name='TB PCR TEST',
			lab_number="123",
			site="chest",
		)
		lt.observation_set.create(
			observation_datetime=yesterday,
			reported_datetime=now,
			observation_value="The PCR to detect M.tuberculosis complex was~POSITIVE",
			observation_name='TB PCR'
		)

	def test_creates_tb_episodes_if_needed(self):
		self.create_positive_tb_test()
		self.cmd.handle()
		self.assertTrue(
			self.patient.episode_set.filter(
				category_name=episode_categories.TbEpisode.display_name
			).exists()
		)

	def test_does_not_create_tb_episode_if_one_already_exists(self):
		self.create_positive_tb_test()
		self.patient.episode_set.create(
			category_name=episode_categories.TbEpisode.display_name
		)
		self.cmd.handle()
		self.assertEqual(
			self.patient.episode_set.filter(
				category_name=episode_categories.TbEpisode.display_name
			).count(),
			1
		)

	def test_does_not_create_tb_episode_if_not_needed(self):
		self.cmd.handle()
		self.assertFalse(
			self.patient.episode_set.filter(
				category_name=episode_categories.TbEpisode.display_name
			).exists()
		)
