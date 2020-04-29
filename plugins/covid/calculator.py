"""
Calculates statistics for the Covid 19 Dashboard
"""
import collections

from django.utils import timezone

from elcid.models import Demographics
from plugins.labtests.models import LabTest

from plugins.covid import lab, models

class Day(object):

    def __init__(self):
        self.tests_ordered     = 0
        self.tests_resulted    = 0
        self.patients_positive = 0
        self.patients_resulted = 0
        self.deaths            = 0



def calculate_daily_reports():
    """
    Calculate five numbers for each day:

    - Tests ordered
    - Tests resulted
    - Patients first resulted
    - Patients first positive
    - Deaths
    """
    days                   = collections.defaultdict(Day)
    positive_patients_seen = set()
    resulted_patients_seen = set()

    coronavirus_tests = LabTest.objects.filter(
        test_name__in=lab.COVID_19_TEST_NAMES
    )
    coronavirus_tests = coronavirus_tests.order_by('datetime_ordered')

    first_test_date = LabTest.objects.filter(
        test_name__in=lab.COVID_19_TEST_NAMES).order_by(
            'datetime_ordered').first().datetime_ordered.date()

    for test in coronavirus_tests:
        days[test.datetime_ordered.date()].tests_ordered += 1

        if lab.resulted(test):
            day = lab.get_resulted_date(test)

            days[day].tests_resulted += 1

            if test.patient_id in resulted_patients_seen:
                pass # This patient has already had a result, we only count them once
            else:
                resulted_patients_seen.add(test.patient_id)
                days[day].patients_resulted += 1

            if lab.positive(test):
                if test.patient_id in positive_patients_seen:
                    continue # This is not the first positive test so ignore it
                else:
                    positive_patients_seen.add(test.patient_id)
                    days[day].patients_positive += 1
                    covid_patient = models.CovidPatient(
                        patient=test.patient, date_first_positive=day
                    )
                    covid_patient.save()


    deceased_patients = Demographics.objects.filter(
        death_indicator=True,
        date_of_death__gte=first_test_date,
        patient_id__in=positive_patients_seen
    )
    for demographic in deceased_patients:
        days[demographic.date_of_death].deaths += 1

    for date, day in days.items():
        covid_day = models.CovidReportingDay(
            date=date,
            tests_ordered=day.tests_ordered,
            tests_resulted=day.tests_resulted,
            patients_resulted=day.patients_resulted,
            patients_positive=day.patients_positive,
            deaths=day.deaths
        )
        covid_day.save()


def calculate():
    """
    Main entrypoint for calculating figures related to Covid 19.
    """
    models.CovidDashboard.objects.all().delete()
    models.CovidReportingDay.objects.all().delete()
    models.CovidPatient.objects.all().delete()

    calculate_daily_reports()
    dashboard = models.CovidDashboard(last_updated=timezone.now())
    dashboard.save()
