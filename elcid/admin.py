"""
Admin for elcid fields
"""
from django.contrib import admin
from reversion import models as rmodels
from opal import models as omodels
from elcid import models as emodels
from opal.admin import PatientAdmin as OldPatientAdmin


class PatientAdmin(OldPatientAdmin):
    actions = ["refresh_lab_tests"]

    def refresh_lab_tests(self, request, queryset):
        for patient in queryset:
            emodels.UpstreamLabTest.refresh_lab_tests(patient, request.user)
    refresh_lab_tests.short_description = "Load in lab tests from upstream"


admin.site.register(rmodels.Version, admin.ModelAdmin)
admin.site.register(rmodels.Revision, admin.ModelAdmin)
admin.site.unregister(omodels.Patient)
admin.site.register(omodels.Patient, PatientAdmin)
