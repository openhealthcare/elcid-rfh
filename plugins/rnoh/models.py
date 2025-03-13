"""
Models for plugins.rnoh
"""
from django.db import models
from opal.core.fields import enum, ForeignKeyOrFreeText
from opal.core import lookuplists
from opal.models import EpisodeSubrecord, PatientSubrecord, Antimicrobial
from elcid.models import MicrobiologyOrganism, PreviousMRN


class RNOHConsultants(lookuplists.LookupList):
    pass


class RNOHDemographics(PreviousMRN, PatientSubrecord):
    _is_singleton = True
    _icon         = 'fa fa-user'

    rnoh_hospital_number = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = 'RNOH Demographics'


class RNOHTeams(PreviousMRN, PatientSubrecord):
    _is_singleton = True
    _icon         = 'fa fa-users'

    new_results     = models.NullBooleanField(blank=True, null=True, verbose_name="New-results")
    pending_ref_lab = models.NullBooleanField(blank=True, null=True, verbose_name="Pending-ref-lab-results")
    outstanding     = models.NullBooleanField(blank=True, null=True)
    mdt_spinal      = models.NullBooleanField(blank=True, null=True, verbose_name="MDT-Spinal")
    mdt_jru         = models.NullBooleanField(blank=True, null=True, verbose_name="MDT-JRU")
    mdt_lru         = models.NullBooleanField(blank=True, null=True, verbose_name="MDT-LRU")
    mdt_upper_limb  = models.NullBooleanField(blank=True, null=True, verbose_name="MDT-Upper-Limb")
    mdt_knee        = models.NullBooleanField(blank=True, null=True, verbose_name="MDT-Knee")
    opat            = models.NullBooleanField(blank=True, null=True, verbose_name="OPAT")
    misc            = models.NullBooleanField(blank=True, null=True, verbose_name="Misc")
    clinic          = models.NullBooleanField(blank=True, null=True)

    class Meta:
        verbose_name = "RNOH Teams"


class OPATEpisodes(PreviousMRN, EpisodeSubrecord):
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
    opat_end_date          = models.DateField(blank=True, null=True, verbose_name="OPAT end date")
    administration         = models.CharField(blank=True, null=True, max_length=200, choices=ADMINISTRATION_CHOICES)
    supply                 = models.CharField(blank=True, null=True, max_length=200, choices=SUPPLY_CHOICES)
    outcome_early          = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_early_date     = models.DateField(blank=True, null=True)
    outcome_one_year       = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_one_year_date  = models.DateField(blank=True, null=True)
    outcome_two_years      = models.CharField(blank=True, null=True, max_length=200, choices=OUTCOME_CHOICES)
    outcome_two_years_date = models.DateField(blank=True, null=True)
    further_information    = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "OPAT Episodes"



class RNOHMicrobiology(PreviousMRN, EpisodeSubrecord):

    _icon = "fa fa-crosshairs"

    BLOOD_CULTURE   = 'Blood Culture'
    GENERIC_CULTURE = 'Culture'
    VIRUS_SCREEN    = 'Respiratory Virus Screen'
    PCR             = 'PCR'

    TEST_NAME_CHOICES = enum(
        BLOOD_CULTURE,
        'Covid-19',
        GENERIC_CULTURE,
        'MRSA Screen',
        'CPE Screen',
        VIRUS_SCREEN,
        'Candida Auris Screen',
        'Serology',
        PCR
    )

    CULTURE_TESTS = [
        BLOOD_CULTURE,
        GENERIC_CULTURE,
        VIRUS_SCREEN,
        PCR
    ]


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
        'CSF',
        'NPS',
        'Blood'
    )

    SITE_CHOICES = enum(
        'Abdomen',
        'Ankle',
        'Arm',
        'Back',
        'Buttock',
        'Calf',
        'Clavicle',
        'C-Spine',
        'Ear',
        'Elbow',
        'Femur',
        'Fibula',
        'Hip',
        'Humerus',
        'Ilium Ischium',
        'Ischial tuberosity',
        'Knee',
        'Leg',
        'L-Spine',
        'Nephrostomy',
        'Pelvis',
        'Pubis',
        'Radius',
        'Sacrum',
        'Shoulder',
        'Spine',
        'Suprapubic',
        'Tibia',
        'Thigh',
        'Throat',
        'T-spine',
        'Ulnar',
        'Wrist'
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
    )

    RESULT_CHOICES = enum(
        'NG',
        'Positive',
        'Negative',
        'Equivocal',
        'Detected',
        'Not Detected'
    )

    SIDE_CHOICES = enum(
        'R', 'L',
        'Anterior', 'Posterior'
    )

    sample_date     = models.DateField(blank=True, null=True)
    test_name       = models.CharField(blank=True, null=True, max_length=200, choices=TEST_NAME_CHOICES)
    hospital        = models.CharField(blank=True, null=True, max_length=255)
    number_positive = models.IntegerField(blank=True, null=True)
    number_samples  = models.IntegerField(blank=True, null=True)
    sample_type     = models.CharField(blank=True, null=True, max_length=200, choices=SAMPLE_TYPE_CHOICES)
    side            = models.CharField(blank=True, null=True, max_length=100, choices=SIDE_CHOICES)
    site            = models.CharField(blank=True, null=True, max_length=255, choices=SITE_CHOICES)
    bottle          = models.CharField(blank=True, null=True, max_length=200, choices=BOTTLE_CHOICES)
    status          = models.CharField(blank=True, null=True, max_length=200, choices=CULTURE_CHOICES)
    result          = models.CharField(blank=True, null=True, max_length=200, choices=RESULT_CHOICES)
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


class RNOHActions(PreviousMRN, EpisodeSubrecord):

    _icon = 'fa fa-list'

    date_requested     = models.DateField(blank=True, null=True)
    action             = models.TextField(blank=True, null=True)
    person_responsible = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = 'Actions'
