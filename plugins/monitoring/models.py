"""
Models for the monitoring plugin
"""
from django.db import models


class Fact(models.Model):
    """
    A model to store various performance monitoring data
    """
    when        = models.DateTimeField()
    label       = models.CharField(max_length=100, db_index=True)
    value_int   = models.IntegerField(blank=True, null=True)
    value_float = models.FloatField(blank=True, null=True)
    value_str   = models.CharField(max_length=255, blank=True, null=True)


    def val(self):
        if self.value_int is not None:
            return self.value_int
        if self.value_float is not None:
            return self.value_float
        if self.value_str is not None:
            return self.value_str
        raise ValueError('No value set')
