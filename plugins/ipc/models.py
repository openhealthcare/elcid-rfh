"""
Models for the elCID IPC plugin
"""
import datetime

from django.db import models
from django.utils import timezone
from opal.core.fields import enum
from opal.models import EpisodeSubrecord, PatientSubrecord
from elcid.models import OriginalMRN

from plugins.labtests import models as lab_test_models


class InfectionAlert(EpisodeSubrecord, OriginalMRN):
    """
    An individual alert concerning a case of an infection managed
    by the Infection Prevention & Control team.

    Instances of this subrecord are created by background processes
    filtering incoming lab data, and only ever edited by users.
    """
    _icon = 'fa fa-exclamation-triangle'

    MRSA  = 'MRSA'
    CPE   = 'CPE'
    CDIFF = 'DIFF'
    TB    = 'TB'
    VRE   = 'VRE'

    CATEGORY_CHOICES = enum(
        MRSA,
        CPE,
        CDIFF,
        TB,
        VRE
    )

    # Set automatically by processing of lab data
    trigger_datetime = models.DateTimeField(blank=True)
    lab_test         = models.ForeignKey(
        lab_test_models.LabTest, on_delete=models.SET_NULL, blank=True, null=True)
    category         = models.CharField(max_length=255, choices=CATEGORY_CHOICES)

    seen             = models.BooleanField(default=False)
    comments         = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-trigger_datetime']

    def historic(self):
        "Returns true if > 6m old"
        diff = timezone.now() - self.trigger_datetime
        if diff  > datetime.timedelta(days=6*30):
            return True
        return False


class IPCStatus(PatientSubrecord, OriginalMRN):

    _is_singleton = True
    _icon = 'fa fa-list-ul'

    mrsa = models.BooleanField(
        default=False, verbose_name='MRSA'
    )
    mrsa_date = models.DateField(
        blank=True, null=True, verbose_name='MRSA Date'
    )

    mrsa_neg = models.BooleanField(default=False, verbose_name='MRSA Neg')
    mrsa_neg_date = models.DateField(
        blank=True, null=True, verbose_name='MRSA Neg Date'
    )

    reactive = models.BooleanField(default=False)
    reactive_date = models.DateField(blank=True, null=True)

    c_difficile = models.BooleanField(default=False)
    c_difficile_date = models.DateField(blank=True, null=True)

    vre = models.BooleanField(default=False, verbose_name='VRE')
    vre_date = models.DateField(blank=True, null=True, verbose_name='VRE Date')

    vre_neg = models.BooleanField(
        default=False, verbose_name='VRE Neg'
    )
    vre_neg_date = models.DateField(
        blank=True, null=True, verbose_name='VRE Neg Date'
    )

    carb_resistance = models.BooleanField(default=False)
    carb_resistance_date = models.DateField(
        blank=True, null=True
    )

    contact_of_carb_resistance = models.BooleanField(default=False)
    contact_of_carb_resistance_date = models.DateField(
        blank=True, null=True
    )

    acinetobacter = models.BooleanField(default=False)
    acinetobacter_date = models.DateField(blank=True, null=True)

    contact_of_acinetobacter = models.BooleanField(default=False)
    contact_of_acinetobacter_date = models.DateField(blank=True, null=True)

    cjd = models.BooleanField(default=False, verbose_name='CJD')
    cjd_date = models.DateField(
        blank=True, null=True, verbose_name='CJD Date'
    )

    candida_auris = models.BooleanField(default=False)
    candida_auris_date = models.DateField(blank=True, null=True)

    contact_of_candida_auris = models.BooleanField(default=False)
    contact_of_candida_auris_date = models.DateField(blank=True, null=True)

    multi_drug_resistant_organism = models.BooleanField(default=False)
    multi_drug_resistant_organism_date = models.DateField(blank=True, null=True)

    covid_19 = models.BooleanField(default=False, verbose_name='Covid-19')
    covid_19_date = models.DateField(
        blank=True, null=True, verbose_name='Covid-19 Date'
    )

    contact_of_covid_19 = models.BooleanField(
        default=False, verbose_name='Contact of Covid-19'
    )
    contact_of_covid_19_date = models.DateField(
        blank=True, null=True, verbose_name='Contact of Covid-19 Date'
    )

    other = models.CharField(blank=True, null=True, max_length=256)
    other_date = models.DateField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'IPC Portal Status'
