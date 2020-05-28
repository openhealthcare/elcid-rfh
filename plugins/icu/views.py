"""
Views for the ICU plugin
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from plugins.icu import constants
from plugins.icu.models import ICUWard, ICUHandoverLocation


class ICUDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'icu/dashboard.html'

    def get_ward_info(self, ward_name):
        """
        Given a WARD_NAME string, return summary info about that ICU ward
        """
        beds = ICUWard.objects.get(name=ward_name).beds
        patient_count = ICUHandoverLocation.objects.filter(ward=ward_name).count()

        info = {
            'name'         : ward_name,
            'beds'         : beds,
            'patient_count': patient_count,
        }
        return info

    def get_context_data(self, *a, **k):
        context = super(ICUDashboardView, self).get_context_data(*a, **k)
        wards = []
        for ward_name in constants.WARD_NAMES:
            wards.append(self.get_ward_info(ward_name))

        context['wards'] = wards
        return context
