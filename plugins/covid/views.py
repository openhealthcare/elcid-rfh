"""
Views for our covid plugin
"""
from django.views.generic import TemplateView

from elcid import patient_lists

from plugins.covid.models import CovidDashboard

class CovidDashboardView(TemplateView):
    template_name = 'covid/dashboard.html'

    def get_context_data(self, *a, **k):
        context = super(CovidDashboardView, self).get_context_data(*a, **k)

        dashboard = CovidDashboard.objects.first()

        context['patients_tested'] = dashboard.patients_tested
        context['positive_count']  = dashboard.positive
        context['negative_count']  = dashboard.negative

        context['icu_south_count']         = patient_lists.ICU().get_queryset().count()
        context['icu_east_count']          = patient_lists.ICUEast().get_queryset().count()
        context['icu_west_count']          = patient_lists.ICUWest().get_queryset().count()
        context['shdu_count']              = patient_lists.ICUSHDU().get_queryset().count()
        context['non_canonical_icu_count'] = patient_lists.NonCanonicalICU().get_queryset().count()
        context['covid_non_icu_count']     = patient_lists.Covid19NonICU().get_queryset().count()

        context['icu_total'] = sum([
            context['icu_south_count'],
            context['icu_east_count'],
            context['icu_west_count'],
            context['shdu_count'],
            context['non_canonical_icu_count']
        ])

        return context
