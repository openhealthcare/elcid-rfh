"""
Admin for elCID models
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from opal import models as omodels
from opal.admin import PatientAdmin as OldPatientAdmin, PatientSubrecordAdmin
from django.urls import reverse
from intrahospital_api import loader
from intrahospital_api import models as imodels


class TaggingListFilter(admin.SimpleListFilter):
    """
    A Django Admin filter used by the Patient admin. It allows the user to
    Filter patients by the teams they are, or have been on.
    """
    title          = 'team'
    parameter_name = 'team'

    def lookups(self, request, model_admin):
        """
        Return a list of filter options to display in the Django Admin sidebar
        """
        tags = omodels.Tagging.objects.values_list(
            'value', flat=True
        ).distinct()
        result = []
        for i in tags:
            current_name = "{} - current".format(i)
            old_name = "{} - previously".format(i)
            result.append((current_name.replace(" ", ""), current_name,))
            result.append((old_name.replace(" ", ""), old_name,))

        return result

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        value = self.value()
        if value:
            if value.endswith("-current"):
                value = value.replace("-current", "")
                tagging_qs = omodels.Tagging.objects.filter(
                    value=value, archived=False
                )
                return omodels.Patient.objects.filter(
                    episode__tagging__in=tagging_qs
                ).distinct()
            else:
                value = value.replace("-previously", "")
                tagging_qs = omodels.Tagging.objects.filter(
                    value=value, archived=True
                )
                return omodels.Patient.objects.filter(
                    episode__tagging__in=tagging_qs
                ).distinct()
        return omodels.Patient.objects.all()


class PatientAdmin(OldPatientAdmin):
    actions = ["refresh_lab_tests"]
    list_filter = (TaggingListFilter,)
    list_display = (
        '__str__',
        'patient_detail_link',
        'upstream_lab_results',
    )

    def refresh_lab_tests(self, request, queryset):
        for patient in queryset:
            loader.load_patient(patient, run_async=False)

    refresh_lab_tests.short_description = "Load in lab tests from upstream"

    def upstream_lab_results(self, obj):
        hospital_number = obj.demographics_set.first().hospital_number
        url = reverse(
            'raw_lab_tests', kwargs=dict(hospital_number=hospital_number)
        )
        return format_html("<a href='{url}'>Raw Lab Tests</a>", url=url)


class PatientLoadAdmin(admin.ModelAdmin):
    list_filter = ['state']
    ordering = ('-started',)


class BatchPatientLoadAdmin(PatientLoadAdmin):
    list_display = [
        "__str__",
        "service_name",
        "started",
        "stopped",
        "state",
        "count"
    ]


class InitialPatientLoadAdmin(PatientSubrecordAdmin, PatientLoadAdmin):
    list_display = [
        "__str__", "patient_details", "started", "stopped", "state"
    ]

    def patient_details(self, obj):
        demographics = obj.patient.demographics_set.first()

        return "%s (%s %s)" % (
            demographics.hospital_number,
            demographics.first_name,
            demographics.surname
        )


admin.site.unregister(omodels.Patient)
admin.site.unregister(imodels.InitialPatientLoad)
admin.site.register(omodels.Patient, PatientAdmin)
admin.site.register(imodels.InitialPatientLoad, InitialPatientLoadAdmin)
admin.site.register(imodels.BatchPatientLoad, BatchPatientLoadAdmin)
