"""
Views for our covid plugin
"""
import collections
import csv
import datetime
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.views.generic import TemplateView, View, DetailView

from opal import models as opal_models
from elcid import patient_lists
from plugins.admissions import constants as admission_constants
from plugins.admissions.models import Encounter
from plugins.icu.models import ICUHandover
from plugins.labtests.models import Observation

from plugins.covid import models, constants, lab



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

    def get_weekly_age_shift(self):
        covid_positives_age_date_range = models.CovidPositivesAgeDateRange.objects.order_by(
            "date_start"
        )
        ages = collections.defaultdict(list)
        ages_as_percent = collections.defaultdict(list)
        week_label = []
        for cvadr in covid_positives_age_date_range:
            for field_name in cvadr.AGE_RANGES_TO_START_END.keys():
                field_label = cvadr._meta.get_field(field_name).verbose_name
                field_value = getattr(cvadr, field_name)
                if cvadr.is_significant():
                    ages[field_label].append(field_value)
                    ages_as_percent[field_label].append(cvadr.as_percent(field_value))
                else:
                    ages[field_label].append(0)
                    ages_as_percent[field_label].append(0)
            from_date = cvadr.date_start.strftime("%-d %b")
            to_date = cvadr.date_end.strftime("%-d %b")
            week_label.append(f"{from_date} - {to_date}")
        columns = [['x'] + [i+1 for i in range(len(week_label))]]
        for field_name, values in ages_as_percent.items():
            columns.append([field_name] + values)
        return json.dumps({
            "data": {
                'x': "x",
                'columns': columns,
                'type': 'bar',
                'groups': [
                    list(ages.keys())
                ]
            },
            "axis": {
                "x": {
                    "type": 'category',
                    "tick": {
                        "rotate": 45,
                        "multiline": False
                    }
                },
                "y": {
                    "min": 0,
                    "max": 100,
                    "padding": {"top": 0, "bottom": 0}
                }
            },
            'bar': {
                'width': {
                    'ratio': 0.9
                }
            },
            # These are used in js to calculate the tooltip
            'extra': {
                'raw_values': ages,
                'week_label': week_label
            }
        })

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

        day_before = datetime.date.today() - datetime.timedelta(days=1)
        yesterday = models.CovidReportingDay.objects.filter(date=day_before).first()

        # this should always be the case in prod but is not in dev.
        if not yesterday:
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

        context["weekly_age_change"] = self.get_weekly_age_shift()

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
        context['take7_data'] = [['x'] + ticks[-7:], ['7 Day Take'] + take_timeseries[-7:]]

        context['covid_data'] = [ticks, covid_timeseries, covid_avg]
        context['covid7_data'] = [['x'] + ticks[-7:], ['7 Day Covid Take'] + covid_timeseries[-7:]]

        context['non_covid_data'] = [ticks, non_covid_timeseries, non_covid_avg]
        context['non_covid7_data'] = [['x'] + ticks[-7:], ['7 Day Non Covid Take'] + non_covid_timeseries[-7:]]
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
#        ).exclude(
#            patient__demographics__death_indicator=True
        ).filter(
            # Have they ever even been to the Free or are they
            # Barnet / Chase Farm only?
            patient__encounters__pv1_3_building='RFH'
        ).order_by('-date_first_positive').distinct()

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        covid_patients = self.get_queryset()
        patients = []
        other_patients = []

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
            else:
                other_patients.append(
                     {
                        'covid_patient' : covid_patient,
                        'ticker'        : lab.get_covid_result_ticker(covid_patient.patient),
                        'demographics'  : covid_patient.patient.demographics,
                        'encounter'     : None
                    }
                )

        context['patients'] = patients
        context['other_patients'] = other_patients
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
        'post_code',
        'height',
        'weight',
        'hospital_site',
        'hypertension',
        'ace_inhibitor',
        'angiotension_blocker',
        'nsaid',
        'ihd',
        'heart_failure',
        'arrhythmia',
        'cerebrovascular_disease',
        'type_1_diabetes',
        'type_2_diabetes',
        'copd',
        'asthma',
        'ild',
        'other_lung_condition',
        'ckd',
        'active_malignancy',
        'active_malignancy_on_immunosuppression',
        'hiv',
        'autoimmunne_with_immunosuppression',
        'autoimmunne_without_immunosuppression',
        'gord',
        'depression',
        'anxiety',
        'other_mental_health',
        'obesity',
        'dyslipidaemia',
        'anaemia',
        'smoking_status_at_admission',
        'date_of_admission',
        'date_of_discharge',
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
        'admission_wbc',
        'admission_wbc_date',
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
        'admission_temperature',
        'admission_news2',
        'admission_tep_status',
        'admission_maximum_resp_support',
        'admission_max_fio2_non_nc',
        'admission_max_fio2_nc',
        'admission_days_on_cpap',
        'admission_days_on_niv',
        'admission_days_on_iv',
        'admission_days_on_ippv',
        'admission_days_on_oxygen',
        'admission_corticosteroids',
        'admission_other_drugs',
        'last_icu_admission',
        'followup_lymphocytes',
        'followup_lymphocytes_date',
        'followup_neutrophils',
        'followup_neutrophils_date',
        'followup_wbc',
        'followup_wbc_date',
        'followup_crp',
        'followup_crp_date',
        'followup_ferritin',
        'followup_ferritin_date',
        'followup_ddimer',
        'followup_ddimer_date',
        'followup_cardiac_troponin_t',
        'followup_cardiac_troponin_t_date',
        'followup_nt_pro_bnp',
        'followup_nt_pro_bnp_date',
        'followup_alt',
        'followup_alt_date',
        'followup_ast',
        'followup_ast_date',
        'followup_alkaline_phosphatase',
        'followup_alkaline_phosphatase_date',
        'followup_creatinine',
        'followup_creatinin_date',
        'follow_up_date',
        'social_circumstances',
        'shielding_status',
        'changes_to_medication',
        'followup_breathlessness',
        'followup_breathlessness_trend',
        'max_breathlessness',
        'followup_cough',
        'followup_cough_trend',
        'max_cough',
        'followup_fatigue',
        'followup_fatigue_trend',
        'max_fatigue',
        'followup_sleep_quality',
        'followup_sleep_quality_trend',
        'max_sleep_quality',
        'followup_chest_pain',
        'followup_chest_tightness',
        'followup_myalgia',
        'followup_anosmia',
        'followup_loss_of_taste',
        'followup_chills',
        'followup_anorexia',
        'followup_abdominal_pain',
        'followup_diarrhoea',
        'followup_peripheral_oedema',
        'followup_confusion',
        'followup_focal_weakness',
        'followup_back_to_normal',
        'followup_baseline_health_proximity',
        'followup_back_to_work',
        'followup_current_et',
        'followup_mrc_dyspnoea_scale',
        'followup_current_cfs',
        'followup_phq_score',
        'followup_tsq_score',
        'follow_up_outcome'
    ]

    TEST_CODES = [
            ("FULL BLOOD COUNT", ["Lymphocytes", "Neutrophils", "WBC"],),
            ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
            ("IRON STUDIES (FER)", ["Ferritin"]),
            ("D-DIMER", ["D-DIMER"]),
            ("CARDIAC TROPONIN T", ["Cardiac Troponin T"]),
            ("NT PRO-BNP", ["NT Pro-BNP"]),
            ("LIVER PROFILE", ["ALT", "AST", "Alkaline Phosphatase"]),
            ("UREA AND ELECTROLYTES", ["Creatinine"])
        ]

    def get_admission_labs(self, patient, admission_date):

        if admission_date is None:
            return [''] * 24 # empty

        labs = []

        for test_name, observations in self.TEST_CODES:
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

    def get_followup_labs(self, patient, followup_date):
        if followup_date is None:
            return [''] * 22 # empty

        labs = []

        for test_name, observations in self.TEST_CODES:
            for obs_code in observations:

                observation = Observation.objects.filter(
                    test__patient=patient,
                ).filter(
                    test__test_name=test_name
                ).filter(
                    observation_name=obs_code
                ).filter(
                    observation_datetime__gte=followup_date-datetime.timedelta(days=14)
                ).filter(
                    observation_datetime__lte=followup_date+datetime.timedelta(days=14)
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
        contact       = patient.contactinformation_set.get()
        comorbidities = covid_episode.covidcomorbidities_set.get()

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
            contact.postcode,
            call.height,
            call.weight,
            call.hospital_site,
            comorbidities.hypertension,
            comorbidities.ace_inhibitor,
            comorbidities.angiotension_blocker,
            comorbidities.nsaid,
            comorbidities.ihd,
            comorbidities.heart_failure,
            comorbidities.arrhythmia,
            comorbidities.cerebrovascular_disease,
            comorbidities.type_1_diabetes,
            comorbidities.type_2_diabetes,
            comorbidities.copd,
            comorbidities.asthma,
            comorbidities.ild,
            comorbidities.other_lung_condition,
            comorbidities.ckd,
            comorbidities.active_malignancy,
            comorbidities.active_malignancy_on_immunosuppression,
            comorbidities.hiv,
            comorbidities.autoimmunne_with_immunosuppression,
            comorbidities.autoimmunne_without_immunosuppression,
            comorbidities.gord,
            comorbidities.depression,
            comorbidities.anxiety,
            comorbidities.other_mental_health,
            comorbidities.obesity,
            comorbidities.dyslipidaemia,
            comorbidities.anaemia,
            call.admission_status,
            admission.date_of_admission,
            admission.date_of_discharge,
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

        row += [
            admission.systolic_bp,
            admission.diastolic_bp,
            admission.heart_rate,
            admission.respiratory_rate,
            admission.sao2,
            admission.fi02,
            admission.temperature,
            admission.news2,
            admission.tep_status,
            admission.maximum_resp_support,
            admission.max_fio2_non_nc,
            admission.max_fio2_nc,
            admission.days_on_cpap,
            admission.days_on_niv,
            admission.days_on_iv,
            admission.days_on_ippv,
            admission.days_on_oxygen,
            admission.systemic_corticosteroirds,
            admission.other_drugs
            ]

        icu = ICUHandover.objects.filter(patient=patient).last()
        if icu:
            row.append(str(icu.date_itu_admission))
        else:
            row.append("")

        row += self.get_followup_labs(patient, call.when)

        row += [
            call.when,
            call.social_circumstances,
            call.shielding_status,
            call.changes_to_medication,
            call.current_breathlessness,
            call.breathlessness_trend,
            call.max_breathlessness,
            call.current_cough,
            call.cough_trend,
            call.max_cough,
            call.current_fatigue,
            call.fatigue_trend,
            call.max_fatigue,
            call.current_sleep_quality,
            call.sleep_quality_trend,
            call.max_sleep_quality,
            call.chest_pain,
            call.chest_tightness,
            call.myalgia,
            call.anosmia,
            call.loss_of_taste,
            call.chills,
            call.anorexia,
            call.abdominal_pain,
            call.diarrhoea,
            call.peripheral_oedema,
            call.confusion,
            call.focal_weakness,
            call.back_to_normal,
            call.baseline_health_proximity,
            call.back_to_work,
            call.current_et,
            call.mrc_dyspnoea_scale,
            call.current_cfs,
            call.phq_score(),
            call.tsq_score(),
            call.follow_up_outcome
        ]


        return row


    def get(self, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="covid.extract.csv"'

        writer = csv.writer(response)
        writer.writerow(self.HEADERS)

        if self.request.user.username in constants.DOWNLOAD_USERS:

            for patient in models.CovidPatient.objects.all():
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
