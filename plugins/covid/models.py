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
    date            = models.DateField()
    tests_conducted = models.IntegerField()
    tests_positive  = models.IntegerField()
    deaths          = models.IntegerField()


class CovidPatient(models.Model):
    """
    Way to flag that a patient is in our Covid Cohort
    and store some metadata about that case.
    """
    patient             = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='covid_patient'
    )
    date_first_positive = models.DateField()
