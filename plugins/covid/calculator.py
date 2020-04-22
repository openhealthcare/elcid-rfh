"""
Calculates statistics for the Covid 19 Dashboard
"""
import collections

from django.utils import timezone

from elcid.models import Demographics
from plugins.labtests.models import LabTest

from plugins.covid import constants, models

class Day(object):

    def __init__(self):
        self.tests_conducted = 0
        self.tests_positive  = 0
        self.deaths          = 0

    def __str__(self):
        return 'Conducted: {}\n Positive: {}\n Deaths: {}'.format(
            self.tests_conducted, self.tests_positive, self.deaths)


def calculate_daily_reports():
    """
    Calculate three numbers for each day:
    - Tests Conducted
    - Tests First Positive
    - Deaths
    """
    days                   = collections.defaultdict(Day)
    positive_patients_seen = set()

    coronavirus_tests = LabTest.objects.filter(test_name=constants.CORONAVIRUS_TEST_NAME)
    coronavirus_tests.order_by('-datetime_ordered')
    coronavirus_tests.prefetch_related('observation_set')

    first_test_date = LabTest.objects.filter(
        test_name=CORONAVIRUS_TEST_NAME).order_by(
            'datetime_ordered').first().datetime_ordered.date()

    for test in coronavirus_tests:
        day          = test.datetime_ordered.date()
        observation = test.observation_set.filter(
            observation_name=constants.CORONAVIRUS_OBSERVATION_NAME
        )
        if observation.count() == 0:
            continue # Test without a relevant observation, ignore

        result = observation[0].observation_value

        if result in constants.ALL_TEST_VALUES:
            days[day].tests_conducted += 1

            if result in constants.POSITIVE_TEST_VALUES:
                if test.patient_id in positive_patients_seen:
                    continue # Subsequent positive
                else:
                    positive_patients_seen.add(test.patient_id)
                    days[day].tests_positive += 1

    deceased_patients = Demographics.objects.filter(
        death_indicator=True,
        date_of_death__gte=first_test_date,
        patient_id__in=positive_patients_seen
    )
    for demographic in deceased_patients:
        days[demographic.date_of_death].deaths += 1

    for date, day in days.items():
        covid_day = CovidReportingDay(
            date=date,
            tests_conducted=day.tests_conducted,
            tests_positive=day.tests_positive,
            deaths=day.deaths
        )
        covid_day.save()


def calculate():
    """
    Main entrypoint for calculating figures related to Covid 19.
    """
    calculate_daily_reports()

    models.CovidDashboard.objects.all().delete()
    models.CovidReportingDay.objects.all().delete()
    dashboard = models.CovidDashboard(last_updated=timezone.now())
    dashboard.save()
