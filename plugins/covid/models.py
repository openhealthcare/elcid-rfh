"""
Models for the Covid plugin
"""
from django.db import models
from opal.models import Patient


class CovidDashboard(models.Model):
    """
    Stores figures for the Covid 19 Dashboard in the
    database when they take a significant amount of time
    to calculate.
    """
    last_updated = models.DateTimeField()


class CovidReportingDay(models.Model):
    """
    Stores figures for a single day in for our Covid 19 Dashboard
    """
    HELP_DATE              = "Date this data relates to"
    HELP_TESTS_ORDERED     = "Number of COVID 19 tests ordered on this day"
    HELP_TESTS_RESULTED    = "Number of COVID 19 tests reported on this day"
    HELP_PATIENTS_RESULTED = "Number of patients with resulted tests for COVID 19"
    HELP_PATIENTS_POSITIVE = "Number of patients who first had a COVID 19 test positve result on this day"
    HELP_DEATH             = "Number of patients who died on this day having tested positive for COVID 19"

    date              = models.DateField(help_text=HELP_DATE)
    tests_ordered     = models.IntegerField(help_text=HELP_TESTS_ORDERED)
    tests_resulted    = models.IntegerField(help_text=HELP_TESTS_RESULTED)
    patients_resulted = models.IntegerField(help_text=HELP_PATIENTS_RESULTED)
    patients_positive = models.IntegerField(help_text=HELP_PATIENTS_POSITIVE)
    deaths            = models.IntegerField(help_text=HELP_DEATH)


class CovidPatient(models.Model):
    """
    Way to flag that a patient is in our Covid Cohort
    and store some metadata about that case.
    """
    patient             = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='covid_patient'
    )
    date_first_positive = models.DateField()
