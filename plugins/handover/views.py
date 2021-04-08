"""
Views for the handover pluin
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import TemplateView

#from plugins.covid.lab import get_covid_result_ticker

from plugins.handover.models import NursingHandover


class NursingHandoverDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'handover/nursing_dashboard.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        wards = NursingHandover.objects.all().values(
            'ward_code').annotate(total=Count('ward_code')).order_by('ward_code')

        context['wards'] = wards
        return context


class NursingHandoverWardDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'handover/nursing_ward.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        patients = NursingHandover.objects.filter(ward_code=k['ward_code']).order_by('bedno')
        # for patient in patients:
        #     patient.ticker = get_covid_result_ticker(patient.patient)

        context['patients'] = patients
        context['ward_code'] = k['ward_code']

        return context
