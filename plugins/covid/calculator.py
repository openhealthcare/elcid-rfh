"""
Calculates statistics for the Covid 19 Dashboard
"""
import collections
import datetime

from django.utils import timezone

from elcid.models import Demographics
from elcid.utils import timing
from plugins.labtests.models import LabTest

from plugins.covid import constants, lab, models


@timing
def calculate_daily_reports():
    """
    Calculate five numbers for each day:

    - Tests ordered
    - Tests resulted
    - Patients first resulted
    - Patients first positive
    - Deaths
    """
    all_days = collections.defaultdict(models.CovidReportingDay)
    rfh_days = collections.defaultdict(models.CovidReportingDay)
    barnet_days = collections.defaultdict(models.CovidReportingDay)
    positive_patients_seen = set()
    resulted_patients_seen = set()

    print('looking for barnet patients')
    barnet_patient_ids = set(LabTest.objects.filter(
        lab_number__contains="K",
        test_name__in=lab.COVID_19_TEST_NAMES
    ).values_list(
        'patient_id', flat=True
    ).distinct())
    print(f'found {len(barnet_patient_ids)} barnet patients')


    print('looking for rfh patients')
    rfh_patient_ids = set(LabTest.objects.filter(
        lab_number__contains="L",
        test_name__in=lab.COVID_19_TEST_NAMES
    ).values_list(
        'patient_id', flat=True
    ).distinct())
    print(f'found {len(rfh_patient_ids)} rfh patients')

    junk_patient_ids = [
        d.patient_id for d in Demographics.objects.filter(
            hospital_number__in=constants.KNOWN_JUNK_MRNS
        )
    ]

    coronavirus_tests = LabTest.objects.filter(
        test_name__in=lab.COVID_19_TEST_NAMES
    )
    coronavirus_tests = coronavirus_tests.order_by('datetime_ordered').prefetch_related(
        'observation_set'
    )

    first_test_date = coronavirus_tests[0].datetime_ordered.date()

    print(f'looking at {coronavirus_tests.count()} corona tests')
    for test in coronavirus_tests:
        if test.patient_id in junk_patient_ids:
            continue # We are uninterested in tests performed on Scooby Doo etc

        all_days[test.datetime_ordered.date()].tests_ordered += 1
        if test.patient_id in barnet_patient_ids:
            barnet = True
            barnet_days[test.datetime_ordered.date()].tests_ordered += 1

        if test.patient_id in rfh_patient_ids:
            rfh = True
            rfh_days[test.datetime_ordered.date()].tests_ordered += 1


        if lab.resulted(test):
            day = lab.get_resulted_date(test)
            rfh = False
            barnet = False

            if test.patient_id in rfh_patient_ids:
                rfh = True

            if test.patient_id in barnet_patient_ids:
                barnet = True

            all_days[day].tests_resulted += 1

            if rfh:
                rfh_days[day].tests_resulted += 1
            elif barnet:
                barnet_days[day].tests_resulted += 1

            if test.patient_id in resulted_patients_seen:
                pass # This patient has already had a result, we only count them once
            else:
                resulted_patients_seen.add(test.patient_id)
                all_days[day].patients_resulted += 1

            if rfh:
                rfh_days[day].patients_resulted += 1
            elif barnet:
                barnet_days[day].patients_resulted += 1

            if lab.positive(test):
                if test.patient_id in positive_patients_seen:
                    continue # This is not the first positive test so ignore it
                else:
                    positive_patients_seen.add(test.patient_id)
                    all_days[day].patients_positive += 1

                    if rfh:
                        rfh_days[day].patients_positive += 1
                    elif barnet:
                        barnet_days[day].patients_positive += 1

                    models.CovidPatient(
                        patient=test.patient,
                        date_first_positive=day,
                        barnet=barnet,
                        rfh=rfh
                    ).save()

    print("finished creating patients")

    deceased_patients = Demographics.objects.filter(
        death_indicator=True,
        date_of_death__gte=first_test_date,
        patient_id__in=positive_patients_seen
    )
    for demographic in deceased_patients:
        if demographic.patient_id in junk_patient_ids:
            continue # We are uninterested in the death of Scooby Doo etc

        rfh = False
        barnet = False

        if demographic.patient_id in rfh_patient_ids:
            rfh = True

        if demographic.patient_id in barnet_patient_ids:
            barnet = True

        date_of_death = demographic.date_of_death
        all_days[date_of_death].deaths += 1
        if rfh:
            rfh_days[date_of_death].deaths += 1
        elif barnet:
            barnet_days[date_of_death].deaths += 1

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    location_to_dict_of_days = {
        constants.RFH: rfh_days,
        constants.BARNET: barnet_days,
        constants.ALL: all_days,
    }
    for location, dict_of_days in location_to_dict_of_days.items():
        for date, day in dict_of_days.items():
            day.date = date
            day.location = location
        days = list(dict_of_days.values())
        if yesterday not in dict_of_days:
            days.append(
                models.CovidReportingDay(
                    date=yesterday,
                    location=location
                )
            )
        models.CovidReportingDay.objects.bulk_create(days)

@timing
def calculate():
    """
    Main entrypoint for calculating figures related to Covid 19.
    """
    models.CovidDashboard.objects.all().delete()
    models.CovidReportingDay.objects.all().delete()
    models.CovidPatient.objects.all().delete()
    models.CovidPositivesAgeDateRange.objects.all().delete()

    calculate_daily_reports()
    for location in constants.LOCATIONS:
        calculate_week_shift(location)
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

@timing
def calculate_week_shift(location):
    """
    For each week calculates the numbers of patients
    in different age ranges.
    """
    covid_patients = models.CovidPatient.objects.all()
    if location == constants.RFH:
        covid_patients = covid_patients.filter(rfh=True)
    elif location == constants.BARNET:
        covid_patients = covid_patients.filter(barnet=True)

    covid_patients = covid_patients.order_by("date_first_positive").prefetch_related(
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
