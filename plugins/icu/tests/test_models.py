"""
Unittests for icu.models
"""
from opal.core.test import OpalTestCase

from plugins.icu import models


class TestParseLocation(OpalTestCase):

    def test_3_part_location(self):
        location = 'ICU4_South_Bed-15'
        hospital, ward, bed = models.parse_icu_location(location)
        self.assertEqual('ICU4', hospital)
        self.assertEqual('South', ward)
        self.assertEqual('15', bed)

    def test_2_part_location(self):
        location = 'SHDU_Bed-07'
        hospital, ward, bed = models.parse_icu_location(location)
        self.assertEqual(None, hospital)
        self.assertEqual('SHDU', ward)
        self.assertEqual('07', bed)
