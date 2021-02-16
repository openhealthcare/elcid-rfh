"""
Views for our covid plugin
"""
import collections
import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.views.generic import TemplateView, View, DetailView

from opal import models as opal_models
from elcid import patient_lists
from plugins.admissions import constants as admission_constants
from plugins.admissions.models import Encounter

from plugins.covid import models, constants, lab
from plugins.labtests.models import Observation



def rolling_average(series):
    """
    Return a 7 day rolling average for a series
    """
    if len(series) < 7:
        return [0 for i in range(len(series))]

    rolling = [0,0,0,0,0,0]
    for i in range(6, len(series)):
        total = sum(series[i-6:i+1])/7
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

#        yesterday = models.CovidReportingDay.objects.get(date = datetime.date.today() - datetime.timedelta(days=1))
        yesterday = None
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

            positive_timeseries.append(day.patients_positive)
            deaths_timeseries.append(day.deaths)
            ordered_timeseries.append(day.tests_ordered)
            patients_timeseries.append(day.patients_resulted)

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


class CovidAMTDashboardView(TemplateView):
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
        context['covid_data'] = [ticks, covid_timeseries, covid_avg]
        context['non_covid_data'] = [ticks, non_covid_timeseries, non_covid_avg]

        return context


class CovidRecentPositivesView(LoginRequiredMixin, TemplateView):
    template_name = 'covid/recent_positives.html'
    days_back = 10

    def get_queryset(self):
        start = datetime.date.today() - datetime.timedelta(days=self.days_back)

        return models.CovidPatient.objects.filter(
            date_first_positive__gt=start
        ).exclude(
            patient_id=54289 # Test patient
        ).exclude(
            patient__demographics__death_indicator=True
        ).filter(
            # Have they ever even been to the Free or are they
            # Barnet / Chase Farm only?
            patient__encounters__pv1_3_building='RFH'
        ).order_by('-date_first_positive').distinct()

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        covid_patients = self.get_queryset()
        patients = []

        for covid_patient in covid_patients:

            encounter = Encounter.objects.filter(
                patient=covid_patient.patient,
                pv1_3_building='RFH',
                pv1_44_admit_date_time__gt=datetime.date.today() - datetime.timedelta(days=self.days_back+28)
            ).exclude(
                msh_9_msg_type__startswith='S', # Appointment scheduling noise
            ).exclude(
                pv1_2_patient_class='OUTPATIENT'
            ).exclude(
                pv1_2_patient_class='RECURRING'
            ).order_by('-pv1_44_admit_date_time').first()

            if encounter:

                patients.append(
                    {
                        'covid_patient' : covid_patient,
                        'ticker'        : lab.get_covid_result_ticker(covid_patient.patient),
                        'demographics'  : covid_patient.patient.demographics,
                        'encounter'     : encounter.to_dict()
                    }
                )

        context['patients'] = patients
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


class CovidExtractDownloadView(LoginRequiredMixin, View):

    HEADERS = [
        'elcid_id',
        'MRN',
        'date_of_birth',
        'death_indicator',
        'date_of_death',
        'sex',
        'ethnicity_pas',
        'ethnicity_fu',
        'ethnicity_coded',
        'height',
        'weight',
        'date_of_admission',
        'duration_of_symptoms',
        'cough',
        'shortness_of_breath',
        'sore_throat',
        'rhinitis',
        'fever',
        'chills',
        'fatigue',
        'myalgia',
        'headache',
        'anorexia',
        'anosmia',
        'loss_of_taste',
        'diarrhoea',
        'abdominal_pain',
        'chest_pain',
        'chest_tightness',
        'confusion',
        'peripheral_oedema',
        'focal_weakness',
        'admission_clinical_frailty_scale',
        'date_first_positive',
        'admission_lymphocytes',
        'admission_lymphocytes_date',
        'admission_neutrophils',
        'admission_neutrophils_date',
        'admission_crp',
        'admission_crp_date',
        'admission_ferritin',
        'admission_ferritin_date',
        'admission_ddimer',
        'admission_ddimer_date',
        'admission_cardiac_troponin_t',
        'admission_cardiac_troponin_t_date',
        'admission_nt_pro_bnp',
        'admission_nt_pro_bnp_date',
        'admission_alt',
        'admission_alt_date',
        'admission_ast',
        'admission_ast_date',
        'admission_alkaline_phosphatase',
        'admission_alkaline_phosphatase_date',
        'admission_creatinine',
        'admission_creatinin_date',
        'cxr_covid_coding',
        'admission_systolic_bp',
        'admission_diastolic_bp',
        'admission_heart_rate',
        'admission_respiratory_rate',
        'admission_sao2',
        'admission_fio2',
        'temperature'
    ]


    def get_admission_labs(self, patient, admission_date):

        if admission_date is None:
            return [''] * 22 # empty

        labs = []

        test_codes = [
            ("FULL BLOOD COUNT", ["Lymphocytes", "Neutrophils"],),
            ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
            ("IRON STUDIES (FER)", ["Ferritin"]),
            ("D-DIMER", ["D-DIMER"]),
            ("CARDIAC TROPONIN T", ["Cardiac Troponin T"]),
            ("NT PRO-BNP", ["NT Pro-BNP"]),
            ("LIVER PROFILE", ["ALT", "AST", "Alkaline Phosphatase"]),
            ("UREA AND ELECTROLYTES", ["Creatinine"])
        ]

        for test_name, observations in test_codes:
            for obs_code in observations:

                observation = Observation.objects.filter(
                    test__patient=patient,
                ).filter(
                    test__test_name=test_name
                ).filter(
                    observation_name=obs_code
                ).filter(
                    observation_datetime__gte=admission_date
                ).order_by('observation_datetime').first()

                if observation:
                    labs.append(observation.observation_value.split('~')[0])
                    labs.append(observation.observation_datetime)
                else:
                    labs += ["", ""]


        return labs

    def get_row(self, covid_patient):

        patient       = covid_patient.patient
        covid_episode = patient.episode_set.get(category_name='COVID-19')
        demographics  = patient.demographics()

        if covid_episode.covidadmission_set.count() == 1:
            admission = covid_episode.covidadmission_set.get()
        elif covid_episode.covidadmission_set.count() == 0:
            admission = models.CovidAdmission()

        followups = models.CovidFollowUpCall.objects.filter(
            episode=covid_episode
        ).exclude(follow_up_outcome__in=[
            models.CovidFollowUpCall.UNREACHABLE,
            models.CovidFollowUpCall.UNABLE_TO_COMPLETE
        ]).order_by('-when')

        if followups.count() == 0:
            call = models.CovidFollowUpCall()

        if followups.count() > 0:
            call = followups[0]

        row = [
            patient.id,
            demographics.hospital_number,
            str(demographics.date_of_birth),
            demographics.death_indicator,
            str(demographics.date_of_death),
            demographics.sex,
            demographics.ethnicity,
            call.ethnicity,
            call.ethnicity_code,
            call.height,
            call.weight,
            admission.date_of_admission,
            admission.duration_of_symptoms,
            admission.cough,
            admission.shortness_of_breath,
            admission.sore_throat,
            admission.rhinitis,
            admission.fever,
            admission.chills,
            admission.fatigue,
            admission.myalgia,
            admission.headache,
            admission.anorexia,
            admission.anosmia,
            admission.loss_of_taste,
            admission.diarrhoea,
            admission.abdominal_pain,
            admission.chest_pain,
            admission.chest_tightness,
            admission.confusion,
            admission.peripheral_oedema,
            admission.focal_weakness,
            admission.clinical_frailty,
            str(covid_patient.date_first_positive)
        ]

        row += self.get_admission_labs(patient, admission.date_of_admission)

        coded_reports = models.CovidReportCode.objects.filter(
            report__patient_id=patient.id
        )
        row.append(';'.join([report.covid_code for report in coded_reports]))

        row.append([
            admission.systolic_bp,
            admission.diastolic_bp,
            admission.heart_rate,
            admission.respiratory_rate,
            admission.sao2,
            admission.fio2,
            admission,temperature,
        ])

        return row


    def get(self, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="covid.extract.csv"'

        writer = csv.writer(response)
        writer.writerow(self.HEADERS)

        if self.request.user.username in constants.DOWNLOAD_USERS:

            for patient in models.CovidPatient.objects.all()[:10]:
                writer.writerow(self.get_row(patient))

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
