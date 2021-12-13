"""
Generates a standard extract of covid data
"""
import csv
import datetime
import os

from django.conf import settings
from opal import models as opal_models

from elcid.utils import mkdir_p
from plugins.icu.models import ICUHandover
from plugins.labtests.models import Observation

from plugins.covid import models, lab

EXTRACT_FILE_PATH = os.path.join(
    settings.COVID_EXTRACT_LOCATION, 'covid.extract.csv')

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
    'diabetes',
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
    "admission_eosinophils",
    "admission_eosinophils_date",
    "admission_hb",
    "admission_hb_date",
    "admission_platelets",
    "admission_platelets_date",

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
    'admission_albumin',
    'admission_albumin_date',
    'admission_alkaline_phosphatase',
    'admission_alkaline_phosphatase_date',
    'admission_bilirubin',
    'admission_bilirubin_date',
    'admission_creatinine',
    'admission_creatinine_date',
    'admission_urea',
    'admission_urea_date',
    'admission_egfr',
    'admission_egfr_date',

    'admission_inr',
    'admission_inr_date',
    'admission_fibrinogen',
    'admission_fibrinogen_date',
    'admission_glucose',
    'admission_glucose_date',
    'admission_kinase',
    'admission_kinase_date',
    'admission_lactate_dehydrogenase',
    'admission_lactate_dehydrogenase_date',

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

    "followup_eosinophils",
    "followup_eosinophils_date",
    "followup_hb",
    "followup_hb_date",
    "followup_platelets",
    "followup_platelets_date",

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
    'followup_albumin',
    'followup_albumin_date',
    'followup_alkaline_phosphatase',
    'followup_alkaline_phosphatase_date',
    'followup_bilirubin',
    'followup_bilirubin_date',
    'followup_creatinine',
    'followup_creatinin_date',
    'followup_urea',
    'followup_urea_date',
    'followup_egfr',
    'followup_egfr_date',

    'followup_inr',
    'followup_inr_date',
    'followup_fibrinogen',
    'followup_fibrinogen_date',
    'followup_glucose',
    'followup_glucose_date',
    'followup_kinase',
    'followup_kinase_date',
    'followup_lactate_dehydrogenase',
    'followup_lactate_dehydrogenase_date',

    'follow_up_date',
    'smoking_status_at_followup',
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
    ("FULL BLOOD COUNT", ["Lymphocytes", "Neutrophils", "WBC", "Eosinophils", "Hb", "Platelets"],),
    ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
    ("IRON STUDIES (FER)", ["Ferritin"]),
    ("D-DIMER", ["D-Dimer"]),
    ("CARDIAC TROPONIN T", ["Cardiac Troponin T"]),
    ("NT PRO-BNP", ["NT Pro-BNP"]),
    ("LIVER PROFILE", ["ALT", "AST", "Albumin", "Alkaline Phosphatase", "Total Bilirubin"]),
    ("UREA AND ELECTROLYTES", ["Creatinine", "Urea", "eGFR (MDRD)"]),
    ("INR", ["INR"]),
    ("CLOTTING SCREEN", ["Fibrinogen"]),
    ("GLUCOSE", ["Glucose"]),
    ("CREATINE KINASE", ["Creatine Kinase"]),
    ("LACTATE DEHYDROGENASE", ["LD"])
    ]

"""
PROTHROMBIN TIME and INR can be ordered as
PT\T\INR # MRN 50092170
Fibrinogen can be ordered as CLOTING SCREEN
"""


def get_admission_labs(patient, admission_date):

    if admission_date is None:
        return [''] * 48 # empty

    labs = []

    for test_name, observations in TEST_CODES:
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

def get_followup_labs(patient, followup_date):
    if followup_date is None:
        return [''] * 48 # empty

    labs = []

    for test_name, observations in TEST_CODES:
        for obs_code in observations:
# TODO 3 months either side but pick the closest one .
            observation = Observation.objects.filter(
                test__patient=patient,
            ).filter(
                test__test_name=test_name
            ).filter(
                observation_name=obs_code
            ).filter(
                observation_datetime__gte=followup_date-datetime.timedelta(days=42)
            ).filter(
                observation_datetime__lte=followup_date+datetime.timedelta(days=42)
            ).order_by('observation_datetime').first()

            if observation:
                labs.append(observation.observation_value.split('~')[0])
                labs.append(observation.observation_datetime)
            else:
                labs += ["", ""]

    return labs




def get_covid_extract_row(covid_patient):

    patient       = covid_patient.patient
    covid_episode = patient.episode_set.get(category_name='COVID-19')
    demographics  = patient.demographics()
    contact       = patient.contactinformation_set.get()
    comorbidities = covid_episode.covidcomorbidities_set.get()

    if covid_episode.covidadmission_set.count() > 0:
        admission = covid_episode.covidadmission_set.order_by('date_of_admission').last()
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
    ]

    row.append(comorbidities.type_1_diabetes or comorbidities.type_2_diabetes)

    row += [
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

    row += get_admission_labs(patient, admission.date_of_admission)

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

    row += get_followup_labs(patient, call.when)

    row += [
        call.when,
        call.followup_status,
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




def generate_extract_file():
    """
    Creates a weekly Covid extract and places it on disk so the
    user experiences an instant download.
    """
    mkdir_p(settings.COVID_EXTRACT_LOCATION)

    fh = open(EXTRACT_FILE_PATH, 'w')

    writer = csv.writer(fh)
    writer.writerow(HEADERS)

    for patient in models.CovidPatient.objects.all():
        print(patient)
        try:
            writer.writerow(get_covid_extract_row(patient))
        except:
            print(f"Error: Patient {patient.patient.id} {patient.patient.demographics().name}")
            raise

    syndromic = set([e.patient for e in opal_models.Episode.objects.filter(
            category_name='COVID-19', patient__covid_patient__isnull=True)])

    for patient in syndromic:
        writer.writerow(get_covid_extract_row(models.CovidPatient(patient=patient)))
