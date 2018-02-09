"""
Models for tb
"""
from django.db import models as fields
from opal import models
from opal.core import lookuplists


class TBSite(lookuplists.LookupList):
    pass


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


class HistoricalTBContact(models.PatientSubrecord):
    """ This patient has previously been in contact with
        someone who has had TB.

        This is never filled in if the patient
        has previous history with TB as this is superceded
        by that.
    """
    _is_singleton = True




class PersonalTBHistory(models.PatientSubrecord):
    """ This patient has previously had TB
    """
    _is_singleton = True

    TB_TYPES = (
        ("Active", "Active"),
        ("Latent", "Latent"),
        ("Unknown", "Unknown"),
    )

    # at some pont we should wrap these in a duration field
    how_long_ago_years = fields.IntegerField(
        blank=True, null=True
    )
    how_long_ago_months = fields.IntegerField(
        blank=True, null=True
    )
    how_long_ago_days = fields.IntegerField(
        blank=True, null=True
    )

    type_of_tb = fields.CharField(
        blank=True, null=True, max_length=40, choices=TB_TYPES
    )

    sites = fields.ManyToManyField(TBSite, blank=True)

    def to_dict(self, user):
        result = super(PersonalTBHistory, self).to_dict(user)
        result["sites"] = list(self.sites.values_list("name", flat=True))
        return result


class TBHistory(models.PatientSubrecord):
    _icon = 'fa fa-clock-o'
    _title = "History of TB"
    _is_singleton = True

    personal_history_of_tb = fields.TextField(blank=True, null=True, verbose_name="Personal History of TB")
    date_of_previous_tb_infection = fields.CharField(max_length=255, blank=True, null=True, verbose_name="Date of Previous TB")
    other_tb_contact = fields.TextField(blank=True, null=True, verbose_name="Other TB Contact")
    date_of_other_tb_contact = fields.CharField(max_length=255, blank=True, null=True, verbose_name="Date of TB Contact")


class BCG(models.PatientSubrecord):
    _icon = 'fa fa-asterisk'
    _title = "BCG"
    _is_singleton = True
    history_of_bcg = fields.CharField(max_length=255, blank=True, null=True, verbose_name="History Of BCG")
    date_of_bcg = fields.DateField(blank=True, null=True, verbose_name="Date Of BCG")
    bcg_scar = fields.BooleanField(default=False, verbose_name="BCG Scar")
    red_book_documentation_of_bcg_seen = fields.BooleanField(default=False, verbose_name="Red Book Documentation of BCG Seen")
