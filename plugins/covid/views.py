"""
Views for our covid plugin
"""
import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.views.generic import TemplateView, View, DetailView

from opal import models as opal_models
from elcid import patient_lists

from plugins.covid import models, constants


def rolling_average(series):
    """
    Return a 7 day rolling average for a series
    """
    rolling = [0,0,0,0,0,0]
    for i in range(6, len(series)-6):
        total = sum(series[i:i+6])/7
        print(total)
        rolling.append(total)
    return rolling



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
            context[sum_field] = models.CovidReportingDay.objects.filter(
                date__gte=datetime.date(2020, 1, 1),
                date__lt=datetime.date.today() + datetime.timedelta(days=1)
            ).aggregate(Sum(sum_field))['{}__sum'.format(sum_field)]

        yesterday = models.CovidReportingDay.objects.get(date = datetime.date.today() - datetime.timedelta(days=1))
        context['yesterday'] = yesterday

        ticks      = ['x']

        positive_timeseries   = ['Positive Tests']
        deaths_timeseries     = ['Deaths']
        ordered_timeseries    = ['Tests ordered']
        patients_timeseries   = ['Patients tested']
        positivity_timeseries = ['Positivity']

        for day in models.CovidReportingDay.objects.filter(
                date__gte=datetime.date(2020, 1, 1),
                date__lt=datetime.date.today() + datetime.timedelta(days=1)
        ).order_by('date'):

            ticks.append(day.date.strftime('%Y-%m-%d'))

            if day.patients_positive:
                positive_timeseries.append(day.patients_positive)
            else:
                positive_timeseries.append(0)

            if day.deaths:
                deaths_timeseries.append(day.deaths)
            else:
                deaths_timeseries.append(0)

            if day.tests_ordered:
                ordered_timeseries.append(day.tests_ordered)
            else:
                ordered_timeseries.append(0)

            if day.patients_resulted:
                patients_timeseries.append(day.patients_resulted)
            else:
                patients_timeseries.append(0)

            if not day.patients_positive:
                positivity_timeseries.append(0)
            else:
                perc = float("{:.2f}".format((day.patients_positive / day.patients_resulted)*100))
                positivity_timeseries.append(perc)


        context['positive_data']   = [ticks, positive_timeseries]
        context['deaths_data']     = [ticks, deaths_timeseries]
        context['orders_data']     = [ticks, ordered_timeseries]
        context['patients_data']   = [ticks, patients_timeseries]
        context['positivity_data'] = [ticks, positivity_timeseries]

        context['can_download'] = self.request.user.username in constants.DOWNLOAD_USERS

        return context


class CovidAMTDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'covid/amt_dashboard.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        ticks = ['x']
        take_timeseries = ['Acute Take']
        take_avg        = ['Acute Take 7 Day Rolling Average']
        covid_timeseries = ['Acute Covid Take']
        covid_avg        = ['Acute Covid Take 7 Day Rolling Average']
        non_covid_timeseries = ['Acute Non Covid Take']
        non_covid_avg        = ['Acute Non Covid Take 7 Day Rolling Average']

        for day in models.CovidAcuteMedicalDashboardReportingDay.objects.all().order_by('date'):
            ticks.append(day.date.strftime('%Y-%m-%d'))

            take_timeseries.append(day.patients_referred)
            covid_timeseries.append(day.covid)
            non_covid_timeseries.append(day.non_covid)

        take_avg += rolling_average(take_timeseries[1:])
        covid_avg += rolling_average(covid_timeseries[1:])
        non_covid_avg += rolling_average(non_covid_timeseries[1:])

        context['take_data'] = [ticks, take_timeseries, take_avg]
        print(context['take_data'])
        context['covid_data'] = [ticks, covid_timeseries, covid_avg]
        context['non_covid_data'] = [ticks, non_covid_timeseries, non_covid_avg]

        return context


class CovidCohortDownloadView(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="covid.cohort.csv"'

        writer = csv.writer(response)
        writer.writerow(['elcid_id', 'MRN', 'Name', 'date_first_positive'])

        if self.request.user.username in constants.DOWNLOAD_USERS:
            for patient in models.CovidPatient.objects.all():
                demographics = patient.patient.demographics()
                writer.writerow([
                    patient.patient_id,
                    demographics.hospital_number,
                    demographics.name,
                    str(patient.date_first_positive)
                ])

        return response


class CovidLetter(LoginRequiredMixin, DetailView):
    # accessed at /letters/#/covid/letter/10/
    model         = models.CovidFollowUpCall
    template_name = 'covid/letters/covid.html'

    def get_context_data(self, *a, **k):
        ctx = super().get_context_data(*a, **k)
        ctx['today'] = datetime.date.today()
        return ctx


class CovidFollowupLetter(LoginRequiredMixin, DetailView):
    # accessed at /letters/#/covid-followup/letter/10/
    model         = models.CovidFollowUpCallFollowUpCall
    template_name = 'covid/letters/covid_followup.html'


class CovidSixMonthFollowupLetter(LoginRequiredMixin, DetailView):
    # accessed at /letters/#/covid-followup/letter/10/
    model         = models.CovidSixMonthFollowUp
    template_name = 'covid/letters/covid_six_month_followup.html'
