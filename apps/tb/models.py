"""
Models for tb
"""
from django.db import models as fields
from opal.core.fields import ForeignKeyOrFreeText
from opal.core import lookuplists
from opal import models


class SocialHistory(models.EpisodeSubrecord):
    _is_singleton = True
    _title = 'Social History'
    _icon = 'fa fa-clock-o'

    notes                = fields.TextField(blank=True, null=True)
    drinking             = fields.CharField(max_length=250, blank=True, null=True, verbose_name="Alcohol")
    alcohol_dependent    = fields.NullBooleanField()
    smoking              = fields.CharField(max_length=250, blank=True, null=True)
    occupation           = fields.TextField(blank=True, null=True)
    homelessness         = fields.TextField(blank=True, null=True)
    intravenous_drug_use = fields.CharField(max_length=250, blank=True, null=True)
    incarceration        = fields.CharField(max_length=250, blank=True, null=True)
    arrival_in_the_uk    = fields.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Year of arrival in the UK"
    )


class PatientConsultation(models.PatientConsultation):
    pass


class ContactDetails(models.PatientSubrecord):
    _is_singleton = True
    _advanced_searchable = False
    _icon = 'fa fa-phone'
    _title = 'Contact Details'

    telephone = fields.CharField(blank=True, null=True, max_length=50)
    address = fields.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Contact details"


class TBSite(lookuplists.LookupList):
    pass


class TBTreatmentCentre(lookuplists.LookupList):
    pass


class TBHistory(models.PatientSubrecord):
    """ Used if the person has clicked that they
        have a personal history of TB in the
        initial assessment form
    """
    _icon = 'fa fa-clock-o'
    _title = "History of TB"
    _is_singleton = True

    TB_TYPES = (
        ("Active", "Active",),
        ("Latent", "Latent",),
        ("Unknown", "Unknown",),
    )

    NONE = "None"

    PREVIOUS_CONTACT = (
        ("Personal", "Personal",),
        ("Other", "Other",),
        (NONE, NONE,),
    )

    _is_singleton = True
    previous_tb_contact = fields.CharField(
        blank=True,
        choices=PREVIOUS_CONTACT,
        default=NONE,
        max_length=100
    )
    how_long_ago_years = fields.IntegerField(
        blank=True, null=True
    )
    how_long_ago_months = fields.IntegerField(
        blank=True, null=True
    )
    how_long_ago_days = fields.IntegerField(
        blank=True, null=True
    )
    tb_type = fields.CharField(
        blank=True,
        null=True,
        choices=TB_TYPES,
        max_length=256
    )
    site_of_tb = ForeignKeyOrFreeText(TBSite)
    country_treated = ForeignKeyOrFreeText(models.Destination)
    treatment_centre = ForeignKeyOrFreeText(TBTreatmentCentre)
    details = fields.TextField(default="")


class BCG(models.PatientSubrecord):
    _icon = 'fa fa-asterisk'
    _title = "BCG"
    _is_singleton = True
    history_of_bcg = fields.CharField(max_length=255, blank=True, null=True, verbose_name="History Of BCG")
    date_of_bcg = fields.DateField(blank=True, null=True, verbose_name="Date Of BCG")
    bcg_scar = fields.BooleanField(default=False, verbose_name="BCG Scar")
    red_book_documentation_of_bcg_seen = fields.BooleanField(default=False, verbose_name="Red Book Documentation of BCG Seen")
