"""
Unittests for plugins.covid.calculator
"""
from opal.core.test import OpalTestCase

from plugins.covid import calculator


class DayTestCase(OpalTestCase):

    def test_init(self):
        day = calculator.Day()

        self.assertEqual(0, day.tests_ordered)
        self.assertEqual(0, day.tests_resulted)
        self.assertEqual(0, day.patients_positive)
        self.assertEqual(0, day.patients_resulted)
        self.assertEqual(0, day.deaths)
