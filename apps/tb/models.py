"""
Models for tb
"""
from django.db import models as fields
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
        verbose_name="Year of arrival"
    )

class PatientConsultation(models.PatientConsultation): pass


# class TBHistory(models.PatientSubrecord):
#     _icon = 'fa fa-clock-o'
#     _title = "History of TB"
#     personal_history_of_tb = fields.TextField(blank=True, null=True, verbose_name="Personal History of TB")
#     date_of_previous_tb_infection = fields.CharField(max_length=255, blank=True, null=True, verbose_name="Date of Previous TB")
#     other_tb_contact = fields.TextField(blank=True, null=True, verbose_name="Other TB Contact")
#     date_of_other_tb_contact = fields.CharField(max_length=255, blank=True, null=True, verbose_name="Date of TB Contact")


# class TBSite(LookupList):
#     pass


# class TBLocation(models.EpisodeSubrecord):
#     sites = fields.ManyToManyField(TBSite, blank=True)
#     _is_singleton = True

#     def to_dict(self, user):
#         result = super(TBLocation, self).to_dict(user)
#         result["sites"] = list(self.sites.values_list("name", flat=True))
#         return result
