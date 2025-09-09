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
        'Achieved treatment aim (uncomplicated)',
        'Treatment aim attained (complicated)',
        'Treatment aim not attained',
        'Indeterminate',
        'Died (non OPAT related)',
        'Died (OPAT related)',
        'Readmitted',
        'Transfer to another provider'
    )

    TREATMENT_OUTCOME_CHOICES = enum(
        'Cured',
        'Improved',
        'Death OPAT related',
        'Death unrelated to OPAT',
        'Failed',
        'IPAT',
        'Stopped early for other clinical reasons',
        'Transferred to other hospital',
        'Moved to Palliative list',
    )

    COMPLICATIONS_CHOICES = enum(
        'Allergy',
        'Liver impairment',
        'Renal impairment',
        'Other'
        'Vascular access (infection)',
        'Vascular access (thrombus)',
        'Vascular access (other)',
        'Drug reaction (allergy)',
        'Drug reaction (renal impairment)',
        'Drug reaction (hepatic)',
        'Drug reaction (other)',
        'C difficile diarrhoea',
        'Issue with compliance'
    )

    ADMINISTRATION_CHOICES = enum(
        'Self', 'Family', 'Carer', 'District Nurse', 'HAH', 'Private Local', 'OPAT', 'Local A&E', 'Other'
    )

    SUPPLY_CHOICES = enum(
        'RFH', 'RNOH', 'GP', 'Local hospital', 'Private'
    )

    accepted               = models.NullBooleanField()
    accepted_date          = models.DateField(blank=True, null=True)
    rejected_date          = models.DateField(blank=True, null=True)
    rejection_reason       = models.TextField(blank=True, null=True)
    monitoring             = models.NullBooleanField(blank=True, null=True, default=False)
    decision_making_consultant = models.CharField(blank=True, null=True, max_length=256)
    indication             = ForeignKeyOrFreeText(OPATIndication)
    referral_date          = models.DateField(blank=True, null=True)
    referral_source        = models.CharField(blank=True, null=True, max_length=256)
    admission_date         = models.DateField(blank=True, null=True, verbose_name="Hospital Admission Date")
    discharge_date         = models.DateField(blank=True, null=True, verbose_name="Hospital Discharge Date",
                                              help_text='This date will be used to calculate Bed Days Saved')
    opat_start_date        = models.DateField(blank=True, null=True)
    opat_end_date          = models.DateField(blank=True, null=True, verbose_name="OPAT End Date")
    administration         = models.CharField(blank=True, null=True, max_length=200, choices=ADMINISTRATION_CHOICES)
    supply                 = models.CharField(blank=True, null=True, max_length=200, choices=SUPPLY_CHOICES)
    treatment_outcome      = models.CharField(blank=True, null=True, max_length=200, choices=TREATMENT_OUTCOME_CHOICES)

    # TO be removed
    outcome_one_year       = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    # to be removed
    outcome_one_year_date  = models.DateField(blank=True, null=True)
    complications          = models.CharField(blank=True, null=True, max_length=200, choices=COMPLICATIONS_CHOICES)
    microbiology           = models.TextField(blank=True, null=True, verbose_name="Significant Microbiology Results")


class OPATActions(EpisodeSubrecord):

    _icon = 'fa fa-list'

    date_requested     = models.DateField(blank=True, null=True)
    action             = models.TextField(blank=True, null=True)
    person_responsible = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = 'Actions'


class TherapeuticDrugMonitoring(EpisodeSubrecord):

    _icon = 'fa fa-flask'

    date    = models.DateField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)


class ClinicDates(EpisodeSubrecord):
    _icon = 'fa fa-hospital-o'

    date    = models.DateField(blank=True, null=True)
    details = models.CharField(blank=True, null=True, max_length=200)


class RelevantOpatBackground(EpisodeSubrecord):
    _icon = 'fa fa-history'

    _is_singleton = True

    details = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Relevant Background"
