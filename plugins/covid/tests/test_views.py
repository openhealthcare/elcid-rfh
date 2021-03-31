"""
Tests for plugins.covid.views
"""
import datetime
from django.urls import reverse

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

    def test_rolling_avg_small(self):
        series = [2,3,4]
        rolling = views.rolling_average(series)
        self.assertEqual([0,0,0], rolling)


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


class CovidAMTDashboardViewTestCase(OpalTestCase):


    def test_context_data(self):
        models.CovidAcuteMedicalDashboardReportingDay.objects.create(
            date=datetime.date.today(),
            patients_referred=4,
            covid=2,
            non_covid=2
        )

        view = views.CovidAMTDashboardView()
        view.request = self.rf.get('/covid-amt/')

        ctx = view.get_context_data()

        take_data = [
            ['x', datetime.date.today().strftime('%Y-%m-%d')],
            ['Acute Take', 4],
            ['Acute Take 7 Day Rolling Average', 0]
        ]
        self.assertEqual(take_data, ctx['take_data'])


class CovidDashboardViewTestCase(OpalTestCase):
    def setUp(self):
        self.url = reverse("covid_dashboard")
        # initialise the property
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )

    def test_get(self):
        self.assertEqual(
            self.client.get(self.url).status_code,
            200
        )

    def test_weekly_age_change_render(self):
        today = datetime.date.today()
        start_date = today - datetime.timedelta(7)
        covid_positives_age_date_range = models.CovidPositivesAgeDateRange(
           date_start=start_date, date_end=today
        )
        for field_name in models.CovidPositivesAgeDateRange.AGE_RANGES_TO_START_END.keys():
            setattr(covid_positives_age_date_range, field_name, 30)
        covid_positives_age_date_range.save()
        self.assertEqual(
            self.client.get(self.url).status_code,
            200
        )

