from opal.core.test import OpalTestCase
from plugins.admissions import models

class BedStatusTestCase(OpalTestCase):
	def test_to_location_str_normal(self):
		"""
		Tests that a populated BedStatus outputs a human readable
		location string.
		"""
		bed_status = models.BedStatus(
			hospital_site_description="a hospital description",
			ward_name="some ward name",
			room="some room",
			bed="some bed",
		)
		self.assertEqual(
			bed_status.to_location_str(),
			"a hospital description some ward name some room some bed"
		)
	def test_to_location_str_with_None(self):
		"""
		Tests that a populated BedStatus outputs a human readable
		location string.
		"""
		bed_status = models.BedStatus(
			hospital_site_description=None,
			ward_name="some ward name",
			room="some room",
			bed="some bed",
		)
		self.assertEqual(
			bed_status.to_location_str(),
			"some ward name some room some bed"
		)
		bed_status = models.BedStatus(
			hospital_site_description="a hospital description",
			ward_name="some ward name",
			room=None,
			bed="some bed",
		)
		self.assertEqual(
			bed_status.to_location_str(),
			"a hospital description some ward name some bed"
		)
