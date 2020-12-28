"""
Tests for plugins.covid.views
"""
from opal.core.test import OpalTestCase

from plugins.covid import views


class RollingAverageTestCase(OpalTestCase):

    def test_rolling_avg(self):
        series = [
            3,
            3,
            3,
            3,
            3,
            3,
            3
        ]

        rolling = views.rolling_average(series)

        self.assertEqual([0,0,0,0,0,0,3], rolling)

    def test_moving_avg(self):
        series = [
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            10
        ]

        rolling = views.rolling_average(series)

        self.assertEqual([0,0,0,0,0,0,3,4], rolling)
