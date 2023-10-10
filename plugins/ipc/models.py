"""
Models for the elCID IPC plugin
"""
import datetime

from django.db import models
from django.utils import timezone
from opal.core.fields import enum
from opal.models import EpisodeSubrecord, PatientSubrecord
from elcid.models import PreviousMRN

from plugins.labtests import models as lab_test_models


class InfectionAlert(PreviousMRN, EpisodeSubrecord):
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


class IPCStatus(PreviousMRN, PatientSubrecord):

    _is_singleton = True
    _title = 'IPC Flags'
    _icon = 'fa fa-list-ul'

    FLAGS = {
        'MRSA'                 : 'mrsa',
        'MRSA NEG'             : 'mrsa_neg',
        'Reactive'             : 'reactive',
        'C Diff'               : 'c_difficile',
        'VRE'                  : 'vre',
        'VRE neg'              : 'vre_neg',
        'Carb Res'             : 'carb_resistance',
        'Carb Res contact'     : 'contact_of_carb_resistance',
        'Acinetobacter'        : 'acinetobacter',
        'Acinetobacter contact': 'contact_of_acinetobacter',
        'CJD'                  : 'cjd',
        'Candida Auris'        : 'candida_auris',
        'Candida Auris contact': 'contact_of_candida_auris',
        'MDR'                  : 'multi_drug_resistant_organism',
        'Covid 19'             : 'covid_19',
        'Covid 19 contact'     : 'contact_of_covid_19',

    }

    mrsa = models.BooleanField(
        default=False, verbose_name='MRSA'
    )
    mrsa_date = models.DateField(
        blank=True, null=True, verbose_name='MRSA Date'
    )
    mrsa_lab_numbers = models.TextField(blank=True, null=True)

    mrsa_neg = models.BooleanField(default=False, verbose_name='MRSA Neg')
    mrsa_neg_date = models.DateField(
        blank=True, null=True, verbose_name='MRSA Neg Date'
    )
    mrsa_neg_lab_numbers = models.TextField(blank=True, null=True)

    reactive = models.BooleanField(default=False)
    reactive_date = models.DateField(blank=True, null=True)
    reactive_lab_numbers = models.TextField(blank=True, null=True)

    c_difficile = models.BooleanField(default=False)
    c_difficile_date = models.DateField(blank=True, null=True)
    c_difficile_lab_numbers = models.TextField(blank=True, null=True)

    vre = models.BooleanField(default=False, verbose_name='VRE')
    vre_date = models.DateField(blank=True, null=True, verbose_name='VRE Date')
    vre_lab_numbers = models.TextField(blank=True, null=True)

    vre_neg = models.BooleanField(
        default=False, verbose_name='VRE Neg'
    )
    vre_neg_date = models.DateField(
        blank=True, null=True, verbose_name='VRE Neg Date'
    )
    vre_lab_numbers = models.TextField(blank=True, null=True)

    carb_resistance = models.BooleanField(default=False)
    carb_resistance_date = models.DateField(
        blank=True, null=True
    )
    carb_resistance_lab_numbers = models.TextField(blank=True, null=True)

    contact_of_carb_resistance = models.BooleanField(default=False)
    contact_of_carb_resistance_date = models.DateField(
        blank=True, null=True
    )

    acinetobacter = models.BooleanField(default=False)
    acinetobacter_date = models.DateField(blank=True, null=True)
    acinetobacter_lab_numbers = models.TextField(blank=True, null=True)

    contact_of_acinetobacter = models.BooleanField(default=False)
    contact_of_acinetobacter_date = models.DateField(blank=True, null=True)

    cjd = models.BooleanField(default=False, verbose_name='CJD')
    cjd_date = models.DateField(
        blank=True, null=True, verbose_name='CJD Date'
    )
    cjd_lab_numbers = models.TextField(blank=True, null=True)

    candida_auris = models.BooleanField(default=False)
    candida_auris_date = models.DateField(blank=True, null=True)
    candida_auris_lab_numbers = models.TextField(blank=True, null=True)

    contact_of_candida_auris = models.BooleanField(default=False)
    contact_of_candida_auris_date = models.DateField(blank=True, null=True)

    multi_drug_resistant_organism = models.BooleanField(default=False)
    multi_drug_resistant_organism_date = models.DateField(blank=True, null=True)
    multi_drug_resistant_organism_lab_numbers = models.TextField(blank=True, null=True)

    covid_19 = models.BooleanField(default=False, verbose_name='Covid-19')
    covid_19_date = models.DateField(
        blank=True, null=True, verbose_name='Covid-19 Date'
    )
    covid_19_lab_numbers = models.TextField(blank=True, null=True)

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

    def covid_expired(self):
        if not self.covid_19_date:
            return False

        today = timezone.now().date()
        expiry = today - datetime.timedelta(days=90)
        expired = self.covid_19_date <= expiry

        return expired

    def is_flagged(self):
        """
        Predicate function to return true if this patient has
        any active IPC flags.
        """
        return bool(any(getattr(self, f) for f in self.FLAGS.values()))

    def get_flags(self):
        """
        Return any flags this patient has as a list of strings.
        """
        flags = []
        for label, attr, in self.FLAGS.items():
            if getattr(self, attr):
                sample_date = getattr(self, f"{attr}_date")
                if sample_date:
                    sample_date = sample_date.strftime("%d %b %Y")
                display = f"{sample_date} {label}"
                flags.append(display)
        return flags


class SideroomStatus(PreviousMRN, PatientSubrecord):

    _is_singleton = True
    _icon = 'fa fa-hospital-o'

    RISKS = enum(
        '15', '20', '25', '30', '35', '40', '45', '50'
    )

    # A current risk score for this patient to enable prioritisation
    # in a resource-constrained environment
    risk_score = models.CharField(
        max_length=5, blank=True, null=True, choices=RISKS
    )
    # Issues relevant to this admission, but not of permanant note
    problems = models.TextField(blank=True, null=True)
    # notes on current tasks and actions that may be required
    actions = models.TextField(blank=True, null=True)
