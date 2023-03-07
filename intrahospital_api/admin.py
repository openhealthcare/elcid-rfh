"""
Admin for elcid fields
"""
from django.contrib import admin
from reversion import models as rmodels
from opal import models as omodels
from opal.admin import PatientSubrecordAdmin
from intrahospital_api import models as imodels


class TaggingListFilter(admin.SimpleListFilter):
    title = 'team'
    parameter_name = 'team'

    def lookups(self, request, model_admin):
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
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
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


class PatientLoadAdmin(admin.ModelAdmin):
    list_filter = ['state']
    ordering = ('-started',)


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


admin.site.register(rmodels.Version, admin.ModelAdmin)
admin.site.register(rmodels.Revision, admin.ModelAdmin)
admin.site.unregister(imodels.InitialPatientLoad)
admin.site.register(imodels.InitialPatientLoad, InitialPatientLoadAdmin)
