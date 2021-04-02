"""
Calculates statistics for the Covid 19 Dashboard
"""
import collections
import datetime
from elcid.utils import timing

from django.utils import timezone

from elcid.models import Demographics
from plugins.labtests.models import LabTest

from plugins.covid import constants, lab, models

class Day(object):

    def __init__(self):
        self.tests_ordered     = 0
        self.tests_resulted    = 0
        self.patients_positive = 0
        self.patients_resulted = 0
        self.deaths            = 0


def calculate_daily_reports(tests_qs, location):
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

    junk_patient_ids = [
        d.patient_id for d in Demographics.objects.filter(
            hospital_number__in=constants.KNOWN_JUNK_MRNS
        )
    ]

    tests_qs = tests_qs.filter(
        test_name__in=lab.COVID_19_TEST_NAMES
    )
    coronavirus_tests = tests_qs.order_by('datetime_ordered').prefetch_related(
        'observation_set'
    )

    first_test_date = coronavirus_tests[0].datetime_ordered.date()

    for test in coronavirus_tests:
        if test.patient_id in junk_patient_ids:
            continue # We are uninterested in tests performed on Scooby Doo etc

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
                        patient=test.patient,
                        date_first_positive=day,
                        location=location
                    )
                    covid_patient.save()


    deceased_patients = Demographics.objects.filter(
        death_indicator=True,
        date_of_death__gte=first_test_date,
        patient_id__in=positive_patients_seen
    )
    for demographic in deceased_patients:
        if demographic.patient_id in junk_patient_ids:
            continue # We are uninterested in the death of Scooby Doo etc

        days[demographic.date_of_death].deaths += 1

    for date, day in days.items():
        models.CovidReportingDay(
            location=location,
            date=date,
            tests_ordered=day.tests_ordered,
            tests_resulted=day.tests_resulted,
            patients_resulted=day.patients_resulted,
            patients_positive=day.patients_positive,
            deaths=day.deaths
        ).save()

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    if yesterday not in days:
        models.CovidReportingDay(
            date=yesterday,
            tests_ordered=0,
            tests_resulted=0,
            patients_resulted=0,
            patients_positive=0,
            deaths=0,
            location=location
        ).save()
    calculate_week_shift(location)

@timing
def calculate():
    """
    Main entrypoint for calculating figures related to Covid 19.
    """
    models.CovidDashboard.objects.all().delete()
    models.CovidReportingDay.objects.all().delete()
    models.CovidPatient.objects.all().delete()
    models.CovidPositivesAgeDateRange.objects.all().delete()

    all_lab_tests = LabTest.objects.all()
    barnet_lab_tests = LabTest.objects.filter(lab_number__contains="K")
    rfh_lab_tests = LabTest.objects.filter(lab_number__contains="L")

    calculate_daily_reports(all_lab_tests, "ALL")
    calculate_daily_reports(barnet_lab_tests, "BARNET")
    calculate_daily_reports(rfh_lab_tests, "RFH")

    dashboard = models.CovidDashboard(last_updated=timezone.now())
    dashboard.save()


def get_week_range(first_covid_positive_test):
    """
    Return a list of weeks (a tuple of monday, sunday)
    from the Monday before the first covid positive test
    until the Sunday after today
    """
    first_week_range = get_week(first_covid_positive_test)
    today = datetime.date.today()
    current_week_range = get_week(today)
    iterations = (current_week_range[1] - first_week_range[0]).days
    result = []

    for i in range(0, iterations, 7):
        result.append(get_week(first_week_range[0] + datetime.timedelta(i)))
    return result


def get_week(some_date):
    """
    For a given date return a range of the Monday before to
    the Sunday after.
    """
    for i in range(7):
        previous = some_date - datetime.timedelta(i)
        if previous.isoweekday() == 1:
            return (previous, previous + datetime.timedelta(6),)


def age_range(age):
    ranges = models.CovidPositivesAgeDateRange.AGE_RANGES_TO_START_END
    for title, age_range in ranges.items():
        lower, upper = age_range
        if not upper:
            return title
        if age >= lower and age <= upper:
            return title


def calculate_week_shift(location):
    covid_patients = models.CovidPatient.objects.filter(
        location=location
    ).order_by(
        "date_first_positive"
    ).prefetch_related(
        'patient__demographics_set'
    )
    week_range = get_week_range(covid_patients[0].date_first_positive)

    week_to_age_range = collections.defaultdict(dict)
    # initialise the week range as a list of all weeks between
    # the first positive test and now with 0s as the values
    for week in week_range:
        for age_title in models.CovidPositivesAgeDateRange.AGE_RANGES_TO_START_END.keys():
            week_to_age_range[week][age_title] = 0
    for covid_patient in covid_patients:
        demographics = covid_patient.patient.demographics_set.all()[0]
        if demographics.date_of_birth:
            first_positive = covid_patient.date_first_positive
            demo_age = age_range(demographics.get_age(first_positive))
            week = get_week(first_positive)
            week_to_age_range[week][demo_age] += 1

    for week_range, age_to_demo_ids in sorted(week_to_age_range.items(), key=lambda x: x[0][0]):
        covid_positives_age_date_range = models.CovidPositivesAgeDateRange(
            date_end=week_range[0],
            date_start=week_range[1],
            location=location
        )
        for field_title, count in age_to_demo_ids.items():
            setattr(covid_positives_age_date_range, field_title, count)
        covid_positives_age_date_range.save()
