"""
Models for the Covid plugin
"""
from django.db import models


class CovidDashboard(models.Model):
    """
    Stores figures for the Covid 19 Dashboard in the
    database when they take a significant amount of time
    to calculate.
    """
    patients_tested = models.IntegerField()
    positive        = models.IntegerField()
    negative        = models.IntegerField()
