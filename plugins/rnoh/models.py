"""
Models for plugins.rnoh
"""
from django.db import models
from opal.core.fields import enum, ForeignKeyOrFreeText
from opal.models import EpisodeSubrecord, PatientSubrecord, Antimicrobial

from elcid.models import MicrobiologyOrganism


class RNOHDemographics(PatientSubrecord):
    _is_singleton = True
    _icon         = 'fa fa-user'

    rnoh_hospital_number = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = 'RNOH Demographics'


class OPATEpisodes(EpisodeSubrecord):
    _icon = 'fa fa-pencil-square'

    OUTCOME_CHOICES = enum(
        'Cured',
        'Improved - off antibiotics',
        'Improved - on suppression',
        'Improved - further treatment planned',
        'Failed'
    )

    ADMINISTRATION_CHOICES = enum(
        'Self', 'Family', 'Carer', 'District Nurse', 'HAH', 'Private Local', 'OPAT', 'Local A&E', 'Other'
    )

    SUPPLY_CHOICES = enum(
        'RNOH', 'GP', 'Local hospital', 'Private'
    )

    admission_date         = models.DateField(blank=True, null=True)
    discharge_date         = models.DateField(blank=True, null=True)
    opat_end_date          = models.DateField(blank=True, null=True)
    administration         = models.CharField(blank=True, null=True, max_length=200, choices=ADMINISTRATION_CHOICES)
    supply                 = models.CharField(blank=True, null=True, max_length=200, choices=SUPPLY_CHOICES)
    outcome_early          = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_early_date     = models.DateField(blank=True, null=True)
    outcome_one_year       = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_one_year_date  = models.DateField(blank=True, null=True)
    outcome_two_years      = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_two_years_date = models.DateField(blank=True, null=True)


class RNOHMicrobiology(EpisodeSubrecord):

    _icon = "fa fa-crosshairs"

    TEST_NAME_CHOICES = enum(
        'Culture',
        'MRSA Screen',
        'CPE Screen'
    )

    SAMPLE_TYPE_CHOICES = enum(
        'Tissue',
        'Fluid',
        'Sonication',
        'Pus',
        'W/S',
        'MSU',
        'CSU',
        'Urine',
        'Sputum',
        'Stool',
        'CSF'
    )

    BOTTLE_CHOICES = enum(
        'O2',
        'AnO2',
        'Both',
        'Paed'
    )

    CULTURE_CHOICES = enum(
        'Pend',
        'Flagging',
        'NG 24',
        'NG 48',
        'NG'
    )

    sample_date     = models.DateField(blank=True, null=True)
    test_name       = models.CharField(blank=True, null=True, max_length=200, choices=TEST_NAME_CHOICES)
    hospital        = models.CharField(blank=True, null=True, max_length=255)
    number_positive = models.IntegerField(blank=True, null=True)
    number_samples  = models.IntegerField(blank=True, null=True)
    sample_type     = models.CharField(blank=True, null=True, max_length=200, choices=SAMPLE_TYPE_CHOICES)
    side            = models.CharField(blank=True, null=True, max_length=100, choices=enum('R', 'L'))
    site            = models.CharField(blank=True, null=True, max_length=255)
    bottle          = models.CharField(blank=True, null=True, max_length=200, choices=BOTTLE_CHOICES)
    result          = models.CharField(blank=True, null=True, max_length=200, choices=CULTURE_CHOICES)
    day_positive    = models.IntegerField(blank=True, null=True)
    organism        = ForeignKeyOrFreeText(MicrobiologyOrganism)
    sensitivities   = models.ManyToManyField(
        Antimicrobial, blank=True, related_name="sensitivities"
    )
    resistances = models.ManyToManyField(
        Antimicrobial, blank=True, related_name="resistances"
    )
    notes           = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Microbiology'


class RNOHActions(EpisodeSubrecord):

    _icon = 'fa fa-list'

    date_requested     = models.DateField(blank=True, null=True)
    action             = models.TextField(blank=True, null=True)
    person_responsible = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = 'Actions'
