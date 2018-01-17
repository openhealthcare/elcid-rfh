from django.db import models as fields

"""
Models for tb
"""
# class TBHistory(models.PatientSubrecord):
#     _icon = 'fa fa-clock-o'
#     _title = "History of TB"
#     personal_history_of_tb = fields.TextField(blank=True, null=True, verbose_name="Personal History of TB")
#     date_of_previous_tb_infection = fields.CharField(max_length=255, blank=True, null=True, verbose_name="Date of Previous TB")
#     other_tb_contact = fields.TextField(blank=True, null=True, verbose_name="Other TB Contact")
#     date_of_other_tb_contact = fields.CharField(max_length=255, blank=True, null=True, verbose_name="Date of TB Contact")
#
#
# class TBSite(LookupList):
#     pass
#
#
# class TBLocation(models.EpisodeSubrecord):
#     sites = fields.ManyToManyField(TBSite, blank=True)
#     _is_singleton = True
#
#     def to_dict(self, user):
#         result = super(TBLocation, self).to_dict(user)
#         result["sites"] = list(self.sites.values_list("name", flat=True))
#         return result
