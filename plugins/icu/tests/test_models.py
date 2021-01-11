"""
Unittests for icu.models
"""
from opal.core.test import OpalTestCase

from plugins.icu import models


class TestParseLocation(OpalTestCase):

    def test_3_part_location(self):
        location = 'ICU4_South_Bed-15'
        hospital, ward, bed = models.parse_icu_location(location)
        self.assertEqual(None, hospital)
        self.assertEqual('ICU4_South', ward)
        self.assertEqual('15', bed)

    def test_2_part_location(self):
        location = 'SHDU_Bed-07'
        hospital, ward, bed = models.parse_icu_location(location)
        self.assertEqual(None, hospital)
        self.assertEqual('SHDU', ward)
        self.assertEqual('07', bed)


    def test_4_part_location(self):
        location = 'ICU2_PITU_SR_Bed-33'
        hospital, ward, bed = models.parse_icu_location(location)
        self.assertEqual(None, hospital)
        self.assertEqual('ICU2_PITU_SR', ward)
        self.assertEqual('33', bed)
