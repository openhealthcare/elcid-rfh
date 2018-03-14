"""
Models for tb
"""
from django.db import models as fields
from opal.core.fields import ForeignKeyOrFreeText
from opal.core import lookuplists
from opal import models


class RecreationalDrug(lookuplists.LookupList):
    pass


class SocialHistory(models.EpisodeSubrecord):
    _is_singleton = True
    _title = 'Social History'
    _icon = 'fa fa-clock-o'
    HOMELESSNESS_CHOICES = (
        ("Hostel", "Hostel",),
        ("Sofa surfing", "Sofa surfing",),
        ("Street", "Street",),
    )

    notes = fields.TextField(blank=True, null=True)
    drinking = fields.CharField(
        max_length=250, blank=True, null=True, verbose_name="Alcohol"
    )
    alcohol_dependent = fields.NullBooleanField()
    smoking = fields.CharField(max_length=250, blank=True, null=True)
    occupation = fields.TextField(blank=True, null=True)
    homelessness = fields.TextField(blank=True, null=True)
    homelessness_type = fields.CharField(
        blank=True,
        null=True,
        choices=HOMELESSNESS_CHOICES,
        max_length=256
    )
    recreational_drug_use = fields.CharField(
        max_length=250, blank=True, null=True
    )
    recreational_drug_type = ForeignKeyOrFreeText(RecreationalDrug)
    receiving_treatment = fields.BooleanField(default=False)
    prison_history = fields.CharField(
        max_length=250, blank=True, null=True
    )
    arrival_in_the_uk = fields.CharField(
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

    # telephone = fields.CharField(blank=True, null=True, max_length=50)
    # email = fields.CharField(blank=True, null=True, max_length=255)
    # address = fields.TextField(blank=True, null=True)
    details = fields.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Contact details"


class NextOfKin(models.PatientSubrecord):
    _icon = 'fa fa-child'
    _advanced_searchable = False
    _title = 'Next Of Kin'

    first_name = fields.CharField(blank=True, null=True, max_length=255)
    surname = fields.CharField(blank=True, null=True, max_length=255)
    details = fields.TextField(blank=True, null=True)


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
    PREVIOUS_TB_DIAGNOSIS = "Previous TB Diagnosis"
    PREVIOUS_TB_CONTACT = "Previous TB Contact"

    PREVIOUS_CONTACT = (
        (PREVIOUS_TB_DIAGNOSIS, PREVIOUS_TB_DIAGNOSIS,),
        (PREVIOUS_TB_CONTACT, PREVIOUS_TB_CONTACT,),
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
    how_long_treated_years = fields.IntegerField(
        blank=True, null=True
    )
    how_long_treated_months = fields.IntegerField(
        blank=True, null=True
    )
    how_long_treated_days = fields.IntegerField(
        blank=True, null=True
    )
    tb_type = fields.CharField(
        blank=True,
        null=True,
        choices=TB_TYPES,
        max_length=256,
        verbose_name="TB Type"
    )
    site_of_tb = ForeignKeyOrFreeText(
        TBSite, verbose_name="Site of TB"
    )
    country_treated = ForeignKeyOrFreeText(models.Destination)
    treatment_centre = ForeignKeyOrFreeText(TBTreatmentCentre)
    details = fields.TextField(default="")


class Allergies(models.Allergies):
    pass


class Travel(models.EpisodeSubrecord):
    _icon = 'fa fa-plane'
    _title = "Travel History"

    country = ForeignKeyOrFreeText(models.Destination)
    when = fields.CharField(max_length=255, blank=True)
    duration = fields.CharField(max_length=255, blank=True)
    reason_for_travel = ForeignKeyOrFreeText(models.Travel_reason)


class BCG(models.PatientSubrecord):
    _icon = 'fa fa-asterisk'
    _title = "BCG"
    _is_singleton = True
    BCG_PERIOD = (
        ('Neonatal', 'Neonatal',),
        ('School', 'School',),
        ('Adult', 'Adult',),
        ('Unsure', 'Unsure',),
        ('None', 'None',)
    )
    bcg_type = fields.CharField(
        max_length=255,
        blank=True,
        choices=BCG_PERIOD,
        verbose_name="BCG"
    )
    bcg_scar = fields.BooleanField(default=False, verbose_name="BCG Scar Seen")
    red_book_documentation_of_bcg_seen = fields.BooleanField(
        default=False, verbose_name="Red Book Documentation Of BCG Given"
    )
