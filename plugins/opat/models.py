"""
Models for plugins.opat
"""
from django.db import models
from opal.core.fields import enum, ForeignKeyOrFreeText
from opal.models import EpisodeSubrecord
from opal.core import lookuplists


class OPATIndication(lookuplists.LookupList):
    pass


class OPATRecord(EpisodeSubrecord):
    _icon = 'fa fa-pencil-square'

    class Meta:
        verbose_name = 'OPAT'

    OUTCOME_CHOICES = enum(
        'Cured',
        'Improved - off antibiotics',
        'Improved - on suppression',
        'Improved - further treatment planned',
        'Failed',
        'Indeterminate'
    )

    ADMINISTRATION_CHOICES = enum(
        'Self', 'Family', 'Carer', 'District Nurse', 'HAH', 'Private Local', 'OPAT', 'Local A&E', 'Other'
    )

    SUPPLY_CHOICES = enum(
        'RNOH', 'GP', 'Local hospital', 'Private'
    )

    accepted               = models.NullBooleanField()
    accepted_date          = models.DateField(blank=True, null=True)
    rejected_date          = models.DateField(blank=True, null=True)
    rejection_reason       = models.TextField(blank=True, null=True)
    decision_making_consultant = models.CharField(blank=True, null=True, max_length=256)
    indication             = ForeignKeyOrFreeText(OPATIndication)
    referral_date          = models.DateField(blank=True, null=True)
    referral_source        = models.CharField(blank=True, null=True, max_length=256)
    admission_date         = models.DateField(blank=True, null=True)
    discharge_date         = models.DateField(blank=True, null=True)
    opat_start_date        = models.DateField(blank=True, null=True)
    opat_end_date          = models.DateField(blank=True, null=True)
    administration         = models.CharField(blank=True, null=True, max_length=200, choices=ADMINISTRATION_CHOICES)
    supply                 = models.CharField(blank=True, null=True, max_length=200, choices=SUPPLY_CHOICES)
    outcome_early          = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_early_date     = models.DateField(blank=True, null=True)
    outcome_one_year       = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_one_year_date  = models.DateField(blank=True, null=True)
    outcome_two_years      = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_two_years_date = models.DateField(blank=True, null=True)


class OPATActions(EpisodeSubrecord):

    _icon = 'fa fa-list'

    date_requested     = models.DateField(blank=True, null=True)
    action             = models.TextField(blank=True, null=True)
    person_responsible = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = 'Actions'
