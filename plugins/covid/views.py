"""
Views for our covid plugin
"""
import datetime

from django.db.models import Sum
from django.views.generic import TemplateView

from elcid import patient_lists

from plugins.covid import models

class CovidDashboardView(TemplateView):
    template_name = 'covid/dashboard.html'

    def get_context_data(self, *a, **k):
        context = super(CovidDashboardView, self).get_context_data(*a, **k)

        context['dashboard'] = models.CovidDashboard.objects.first()

        sum_fields = [
            'tests_ordered', 'tests_resulted',
            'patients_resulted', 'patients_positive',
            'deaths'
        ]
        for sum_field in sum_fields:
            context[sum_field] = models.CovidReportingDay.objects.all(
            ).aggregate(Sum(sum_field))['{}__sum'.format(sum_field)]

        yesterday = models.CovidReportingDay.objects.get(date = datetime.date.today() - datetime.timedelta(days=1))
        context['yesterday'] = yesterday

        positive_timeseries = ['Positive Tests']
        positive_ticks      = ['x']

        deaths_timeseries   = ['Deaths']
        deaths_ticks        = ['x']

        for day in models.CovidReportingDay.objects.all().order_by('date'):
            if day.patients_positive:
                positive_ticks.append(day.date.strftime('%Y-%m-%d'))
                positive_timeseries.append(day.patients_positive)

            if day.deaths:
                deaths_ticks.append(day.date.strftime('%Y-%m-%d'))
                deaths_timeseries.append(day.deaths)

        context['positive_data'] = [positive_ticks, positive_timeseries]
        context['deaths_data']   = [deaths_ticks, deaths_timeseries]

        return context
