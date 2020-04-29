"""
Views for our covid plugin
"""
import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.views.generic import TemplateView, View

from elcid import patient_lists

from plugins.covid import models

class CovidDashboardView(LoginRequiredMixin, TemplateView):
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


class CovidCohortDownloadView(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="covid.cohort.csv"'

        writer = csv.writer(response)
        writer.writerow(['elcid_id', 'MRN', 'Name', 'date_first_positive'])
        for patient in models.CovidPatient.objects.all():
            demographics = patient.patient.demographics()
            writer.writerow([
                patient.patient_id,
                demographics.hospital_number,
                demographics.name,
                str(patient.date_first_positive)
            ])

        return response
