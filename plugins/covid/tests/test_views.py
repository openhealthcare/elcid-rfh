"""
Tests for plugins.covid.views
"""
import datetime

from opal.core.test import OpalTestCase

from plugins.covid import views, models


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


class CovidDashboardViewTestCase(OpalTestCase):

    def setUp(self):
        self.yesterday = datetime.date.today()-datetime.timedelta(days=1)

    def test_context_data(self):
        models.CovidReportingDay.objects.create(
            tests_ordered=1, tests_resulted=1,
            patients_resulted=1, patients_positive=1,
            deaths=1,
            date=self.yesterday
        )
        view = views.CovidDashboardView()
        view.request = self.rf.get('/covid-dashboard/')
        view.request.user = self.user

        ctx = view.get_context_data()

        positivity_data = [
            ['x', self.yesterday.strftime('%Y-%m-%d')],
            ['Positive Tests', 1]
        ]
        self.assertEqual(positivity_data, ctx['positive_data'])
