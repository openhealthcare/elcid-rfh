"""
Models for the Covid plugin
"""
from django.db import models
from opal.core.fields import enum
from opal.models import Patient, PatientSubrecord, EpisodeSubrecord
from elcid.models import PreviousMRN


def calculate_phq_score(interest, depressed):
    """
    Some PHQ Scores have the user visible text, some the integer.
    This is an unintended side effect of the way Opal 18.4 adjusted
    the handling of choices fields.

    Calculate the correct score value regardless of how it is stored
    in the database.
    """
    if interest is None or depressed is None:
        return None
    try:
        interest = int(interest)
        depressed = int(depressed)
        return interest + depressed
    except ValueError:
        try:
            return int(interest[1:2]) + int(depressed[1:2])
        except ValueError:
            return None


COVID_CODE_CHOICES = enum(
    'Normal',
    'Classic/Probable',
    'Indeterminate',
    'Non-covid'
)

SMOKING_CHOICES = enum(
    'Never',
    'Ex-smoker',
    'Current',
    'Unknown'
)


class CovidDashboard(models.Model):
    """
    Stores figures for the Covid 19 Dashboard in the
    database when they take a significant amount of time
    to calculate.
    """
    last_updated = models.DateTimeField()


class CovidReportingDay(models.Model):
    """
    Stores figures for a single day in for our Covid 19 Dashboard
    """
    HELP_DATE              = "Date this data relates to"
    HELP_TESTS_ORDERED     = "Number of COVID 19 tests ordered on this day"
    HELP_TESTS_RESULTED    = "Number of COVID 19 tests reported on this day"
    HELP_PATIENTS_RESULTED = "Number of patients with resulted tests for COVID 19"
    HELP_PATIENTS_POSITIVE = "Number of patients who first had a COVID 19 test positve result on this day"
    HELP_DEATH             = "Number of patients who died on this day having tested positive for COVID 19"

    date              = models.DateField(help_text=HELP_DATE)
    tests_ordered     = models.IntegerField(help_text=HELP_TESTS_ORDERED)
    tests_resulted    = models.IntegerField(help_text=HELP_TESTS_RESULTED)
    patients_resulted = models.IntegerField(help_text=HELP_PATIENTS_RESULTED)
    patients_positive = models.IntegerField(help_text=HELP_PATIENTS_POSITIVE)
    deaths            = models.IntegerField(help_text=HELP_DEATH)


class CovidPatient(models.Model):
    """
    Way to flag that a patient is in our Covid Cohort
    and store some metadata about that case.
    """
    patient             = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='covid_patient'
    )
    date_first_positive = models.DateField()


class CovidReportCode(models.Model):
    """
    Store the CovidReport Code of an image report
    """
    report     = models.ForeignKey('imaging.Imaging', on_delete=models.CASCADE)
    covid_code = models.CharField(blank=True, null=True, max_length=10)


class CovidAcuteMedicalDashboardReportingDay(models.Model):
    """
    We prepare a dashboard of the acute medical take as it pertains to
    Covid
    """
    date              = models.DateField()
    patients_referred = models.IntegerField()
    covid             = models.IntegerField()
    non_covid         = models.IntegerField()


class CovidVaccination(PreviousMRN, PatientSubrecord):
    """
    Vaccination details for this patient
    """
    VACCINE_CHOICES = enum(
        'Pfizer-BioNTech',
        'Moderna',
        'Oxford Astrazeneca',
    )
    vaccine     = models.CharField(max_length=200, blank=True, null=True, choices=VACCINE_CHOICES)
    dose_1_date = models.DateField(blank=True, null=True)
    dose_2_date = models.DateField(blank=True, null=True)


class CovidAdmission(PreviousMRN, EpisodeSubrecord):
    """
    An admission to hospital and associated details
    """
    _icon = 'fa fa-hospital-o'

    class Meta:
        verbose_name = 'Admission'

    SYMPTOM_CHOICES = enum(
        'Cough',
        'Shortness of breath',
        'Sore throat',
        'Blocked or runny nose',
        'Fever',
        'Myalgia',
        'Headache',
        'Anorexia',
        'Diarrhoea',
        'Abdominal pain',
        'Chest pain/tightness',
        'Confusion/fuzzy head',
        'Periperal oedema',
        'Focal weakness'
    )

    PLAN_CHOICES = enum(
        'Full escalation',
        'Not for CPR but for ITU'
        'Not for ITU but for NIV/CPAP',
        'Not for ITU or CPAP',
        'Not for ITU, CPAP or NIV'
    )

    MAX_RESP_SUPPORT_CHOICES = enum(
        'No support',
        'O2',
        'CPAP',
        'NIV',
        'IV'
    )

    date_of_admission    = models.DateField(blank=True, null=True)
    date_of_discharge    = models.DateField(blank=True, null=True)

    # Symptoms at admission
    duration_of_symptoms = models.IntegerField(
        blank=True, null=True, verbose_name='Duration In Days At Admissison')
    cough                = models.NullBooleanField()
    shortness_of_breath  = models.NullBooleanField()
    sore_throat          = models.NullBooleanField()
    rhinitis             = models.NullBooleanField(verbose_name="Blocked or runny nose")
    fever                = models.NullBooleanField()
    chills               = models.NullBooleanField(verbose_name="Chills or sweats")
    fatigue              = models.NullBooleanField()
    myalgia              = models.NullBooleanField()
    headache             = models.NullBooleanField()
    anorexia             = models.NullBooleanField()
    anosmia              = models.NullBooleanField(verbose_name="Loss of smell")
    loss_of_taste        = models.NullBooleanField()
    diarrhoea            = models.NullBooleanField()
    abdominal_pain       = models.NullBooleanField()
    chest_pain           = models.NullBooleanField()
    chest_tightness      = models.NullBooleanField()
    confusion            = models.NullBooleanField(help_text='Confusion or fuzzy head')
    peripheral_oedema    = models.NullBooleanField()
    focal_weakness       = models.NullBooleanField()
    other                = models.CharField(
        blank=True, null=True, max_length=255, verbose_name='Other Symptoms')
    predominant_symptom  = models.CharField(
        blank=True, null=True, max_length=200, choices=SYMPTOM_CHOICES)

    # Observations at admisssion
    respiratory_rate     = models.IntegerField(blank=True, null=True, help_text='Breaths/min')
    heart_rate           = models.IntegerField(blank=True, null=True, help_text='Beats/min')
    sao2                 = models.CharField(blank=True, null=True, max_length=255, verbose_name="SaO2")
    fi02                 = models.CharField(
        blank=True, null=True, max_length=255, verbose_name='FiO2',
        help_text="Oxygen flow rate if on nasal specs or non-fixed delivery mask"
    )
    systolic_bp          = models.IntegerField(blank=True, null=True, verbose_name='Systolic BP (mmHg)')
    diastolic_bp         = models.IntegerField(blank=True, null=True, verbose_name='Diastolic BP (mmHg)')
    temperature          = models.FloatField(blank=True, null=True, help_text='oC')
    news2                = models.CharField(blank=True, null=True, max_length=255, verbose_name='NEWS2 Score On Arrival')
    clinical_frailty     = models.CharField(blank=True, null=True, max_length=255, verbose_name='Clinical frailty')

    tep_status           = models.CharField(
        blank=True, null=True, max_length=200, choices=PLAN_CHOICES,
        verbose_name='Treatment Escalation Plan Status'
    )

    # Respiratory support
    maximum_resp_support = models.CharField(
        blank=True, null=True, max_length=200, choices=MAX_RESP_SUPPORT_CHOICES
    )
    max_fio2_non_nc           = models.CharField(blank=True, null=True, max_length=255, verbose_name='Max FiO2 non Nasal Cannula')
    max_fio2_nc               = models.CharField(blank=True, null=True, max_length=255, verbose_name='Max FiO2 if Nasal Cannula')
    days_on_cpap              = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On CPAP')
    days_on_niv               = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On NIV')
    days_on_iv                = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On IV')
    days_on_ippv              = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On IPPV')
    days_on_oxygen            = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On Oxygen')

    final_spo2                = models.CharField(
        blank=True, null=True, max_length=244, verbose_name='Last Available SpO2 Prior To Discharge')
    final_fio2                = models.CharField(
        blank=True, null=True, max_length=244, verbose_name='Last Available FiO2 Prior To Discharge')

    systemic_corticosteroirds = models.NullBooleanField(verbose_name='Treated With Systemic Corticosteroids')

    days_on_optiflow = models.IntegerField(blank=True, null=True,
                                           verbose_name='Total Number Of Days On Optiflow')
    other_drugs      = models.TextField(blank=True, null=True)


class LungFunctionTest(PreviousMRN, EpisodeSubrecord):
    """
    Lung function test results for this patient
    """
    _icon = 'fa fa-crosshairs'

    date    = models.DateField(blank=True, null=True)
    fev1    = models.CharField(blank=True, null=True, max_length=244, verbose_name='FEV1 %')
    fvc     = models.CharField(blank=True, null=True, max_length=244, verbose_name='FVC %')
    lf_dlco = models.CharField(blank=True, null=True, max_length=244, verbose_name='Lung Function DLCO %')


class CovidComorbidities(PreviousMRN, EpisodeSubrecord):
    """
    (Potentially) Relevant conditions and comorbidities
    """
    _icon         = 'fa fa-history'
    _is_singleton = True

    class Meta:
        verbose_name = 'Comorbidities'

    hypertension                           = models.NullBooleanField()
    ace_inhibitor                          = models.NullBooleanField(verbose_name='Current ACEi use')
    angiotension_blocker                   = models.NullBooleanField(verbose_name='Current Angiotension receptor blocker use')
    nsaid                                  = models.NullBooleanField(verbose_name='Current NSAID used')
    ihd                                    = models.NullBooleanField(verbose_name="IHD")
    heart_failure                          = models.NullBooleanField()
    arrhythmia                             = models.NullBooleanField(verbose_name='AF/arrhythmia')
    cerebrovascular_disease                = models.NullBooleanField()
    type_1_diabetes                        = models.NullBooleanField(verbose_name="Type I Diabetes")
    type_2_diabetes                        = models.NullBooleanField(verbose_name="Type II Diabetes")
    copd                                   = models.NullBooleanField(verbose_name='COPD')
    asthma                                 = models.NullBooleanField()
    ild                                    = models.NullBooleanField(verbose_name='ILD')
    other_lung_condition                   = models.NullBooleanField()
    ckd                                    = models.NullBooleanField(verbose_name='CKD')
    active_malignancy                      = models.NullBooleanField()
    active_malignancy_on_immunosuppression = models.NullBooleanField(
        verbose_name='Active Malignancy On Immunosuppression (Includes radiotherapy)')
    hiv                                    = models.NullBooleanField(verbose_name='HIV')
    autoimmunne_with_immunosuppression     = models.NullBooleanField(
        help_text='Autoimmune disease requiring current immunosuppression')
    autoimmunne_without_immunosuppression  = models.NullBooleanField(
        help_text='Autoimmune disease not requiring current immunosuppression')
    gord                                   = models.NullBooleanField(verbose_name='GORD')
    depression                             = models.NullBooleanField()
    anxiety                                = models.NullBooleanField()
    other_mental_health                    = models.NullBooleanField()
    obesity                                = models.NullBooleanField()
    dyslipidaemia                          = models.NullBooleanField()
    anaemia                                = models.NullBooleanField()


class CovidFollowUpCall(PreviousMRN, EpisodeSubrecord):
    """
    A phone call to a patient seeking follow up on their COVID-19 admission
    """
    _icon = 'fa fa-phone'

    ONE_TO_TEN           = enum('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10')
    ONE_TO_NINE          = enum('1', '2', '3', '4', '5', '6', '7', '8', '9')
    MRC_CHOICES          = enum('1', '2', '3', '4', '5', 'N/A')
    ZERO_TO_THREE        = enum(
        '(0) Not At All',
        '(1) Several days',
        '(2) More than half the days',
        '(3) Nearly every day'
    )
    ETHNICITY_CODE       = enum("White", "Black", "Asian", "Other")

    POSITION_CHOICES     = enum('Consultant', 'Registrar', 'Associate Specialist', 'Other')
    HOSP_CHOICES         = enum('RFH', 'Barnet')
    TREND_CHOICES        = enum('Same', 'Better', 'Worse', 'Back to baseline')
    Y_N_NA               = enum('Yes', 'No', 'N/A')
    Y_N_NOT_SURE         = enum('Yes', 'No', 'Not sure')
    LIMITED_BY_CHOICES   = enum('SOB', 'Fatigue', 'Other')

    UNABLE_TO_COMPLETE   = 'Unable to complete'
    UNREACHABLE          = 'Unreachable'
    FOLLOWUP             = 'Further Follow Up'
    DISCHARGE            = 'Discharge'
    FOLLOWUP_CHOICES     = enum(
        UNREACHABLE,
        UNABLE_TO_COMPLETE,
        FOLLOWUP,
        DISCHARGE
    )

    CIRCUMSTANCES_CHOICES = enum(
        'Independent',
        'Family help',
        'Carers',
        'NH/RH'
    )

    EXERCISE_CHOICES = enum(
        'Reduced',
        'Back to baseline',
        'Unlimited'
    )

    CARER_CHOICES = enum(
        'OD',
        'BD',
        'TDS',
        'QDS',
        '24h'
    )

    SHIELDING_CHOICES = enum(
        'Not',
        'Voluntary Shielding',
        'Extremely Vulnerable',
        'Letter Issued by HCP'
    )

    OTHER_SMOKING_CHOICES = enum(
        'Vape',
        'Other drugs'
    )

    REFERRAL_FIELDS = [
        'anticoagulation',
        'cardiology',
        'elderly_care',
        'fatigue_services',
        'hepatology',
        'neurology',
        'primary_care',
        'psychiatry',
        'respiratory',
        'rehabilitation',
    ]


    when               = models.DateTimeField(blank=True, null=True)
    clinician          = models.CharField(blank=True, null=True, max_length=255) # Default to user
    position           =  models.CharField(
        blank=True, null=True, max_length=255, choices=POSITION_CHOICES)
    hospital_site      = models.CharField(
        max_length=255, blank=True, null=True, choices=HOSP_CHOICES
    )

    incomplete_reason  = models.TextField(blank=True, null=True)

    ethnicity = models.CharField(blank=True, null=True, max_length=240)
    ethnicity_code = models.CharField(
        blank=True, null=True, max_length=200, choices=ETHNICITY_CODE
    )
    height    = models.CharField(blank=True, null=True, max_length=20, verbose_name='Height (m)')
    weight    = models.CharField(blank=True, null=True, max_length=20, verbose_name='Weight (kg)')

    social_circumstances = models.CharField(
        blank=True, null=True, max_length=200, choices=CIRCUMSTANCES_CHOICES
    )
    carers               = models.CharField(
        blank=True, null=True, max_length=200, choices=CARER_CHOICES
    )
    shielding_status     = models.CharField( # TODO WHAT ARE THESE
        max_length=200, blank=True, null=True, choices=SHIELDING_CHOICES
    )
    admission_status  = models.CharField(
        blank=True, null=True, max_length=200, choices=SMOKING_CHOICES,
        verbose_name='Smoking status on admission'
    )
    pack_year_history = models.TextField(blank=True, null=True)
    vape              = models.NullBooleanField(verbose_name="Vape Smoked")
    other_drugs       = models.NullBooleanField(verbose_name="Other Drugs Smoked")
    followup_status   = models.CharField(
        blank=True, null=True, max_length=200, choices=SMOKING_CHOICES,
        verbose_name='Smoking status at follow up'
    )

    changes_to_medication     = models.NullBooleanField(
        verbose_name="Changes to medication post discharge")
    medication_change_details = models.TextField(blank=True, null=True)

    current_breathlessness    = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_breathlessness        = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    breathlessness_trend      = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)
    current_cough             = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_cough                 = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    cough_trend               = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)
    current_fatigue           = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_fatigue               = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    fatigue_trend             = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)
    current_sleep_quality     = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_sleep_quality         = models.CharField(
        blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    sleep_quality_trend       = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)

    # Symptoms at follow up
    chest_pain                = models.NullBooleanField(help_text='Chest pain')
    chest_tightness           = models.NullBooleanField(help_text='Chest tightness')
    myalgia                   = models.NullBooleanField()
    anosmia                   = models.NullBooleanField()
    loss_of_taste             = models.NullBooleanField(verbose_name="Loss of taste")
    chills                    = models.NullBooleanField(verbose_name="Chills or sweats")
    anorexia                  = models.NullBooleanField()
    abdominal_pain            = models.NullBooleanField(verbose_name="Abdominal pain")
    diarrhoea                 = models.NullBooleanField()
    peripheral_oedema         = models.NullBooleanField()
    confusion                 = models.NullBooleanField(help_text='Confusion or fuzzy head')
    focal_weakness            = models.NullBooleanField()

    # Quality of life at follow up
    back_to_normal            = models.NullBooleanField(verbose_name="Do you feel back to normal?")
    why_not_back_to_normal    = models.TextField(blank=True, null=True)
    baseline_health_proximity = models.IntegerField(
        blank=True, null=True, verbose_name="How close to 100% of usual health do you feel?")
    back_to_work              = models.CharField(
        verbose_name="If working, are you back to work?",
        blank=True, null=True, max_length=20, choices=Y_N_NA)

    current_et                = models.CharField(
        choices=EXERCISE_CHOICES,
        blank=True, null=True, max_length=50,
        verbose_name="Current ET")

    mrc_dyspnoea_scale        = models.CharField(
        blank=True, null=True, max_length=50, choices=MRC_CHOICES,
        verbose_name="MRC Dyspnoea Scale")
    limited_by                = models.CharField(blank=True, null=True,
                                                 max_length=50, choices=LIMITED_BY_CHOICES)
    current_cfs               = models.CharField(
        blank=True, null=True,
        max_length=50, choices=ONE_TO_NINE, verbose_name="Current Clinical Frailty Score")

    # Psychological scores
    interest                  = models.CharField(
        verbose_name="Little interest or pleasure in doing things",
        blank=True, null=True, max_length=50, choices=ZERO_TO_THREE)
    depressed                 = models.CharField(
        verbose_name="Feeling down, depressed or hopeless",
        blank=True, null=True, max_length=50, choices=ZERO_TO_THREE)

    tsq1 = models.NullBooleanField(
        verbose_name='Upsetting thoughts or memories about your hospital admission that have come into your mind against your will'
    )
    tsq2 = models.NullBooleanField(
        verbose_name='Upsetting dreams about the event'
    )
    tsq3 = models.NullBooleanField(
        verbose_name='Acting or feeling as though it is happening again'
    )
    tsq4 = models.NullBooleanField(
        verbose_name='Feeling upset by reminders of the event'
    )
    tsq5 = models.NullBooleanField(
        verbose_name='Bodily reactions such as fast heartbeat, sweatiness, dizziness when reminded of the event'
    )
    tsq6 = models.NullBooleanField(
        verbose_name='Difficulty falling or staying asleep'
    )
    tsq7 = models.NullBooleanField(
        verbose_name='Irritability or bursts of anger'
    )
    tsq8 = models.NullBooleanField(
        verbose_name='Difficulty concentrating'
    )
    tsq9 = models.NullBooleanField(
        verbose_name='Being more aware of potential danger to yourself and others'
    )
    tsq10 = models.NullBooleanField(
        verbose_name='Being jumpy or startled at something unexpected'
    )

    other_concerns            = models.TextField(blank=True, null=True)

    pulse_oximeter = models.CharField(
        verbose_name="If A&E patient, were you discharged with a pulse oximeter?",
        blank=True, null=True, max_length=20, choices=Y_N_NA)
    haem_anticoag = models.CharField(
        verbose_name="(If patient had PE/DVT), have you been offered an appointment with the haematology team/anticoagulation clinic?",
        blank=True, null=True, max_length=20, choices=Y_N_NA)
    diabetic = models.CharField(
        verbose_name="(If diabetic), were you started on insulin during your admission? If so, do you have support or follow-up from hospital diabetic team/community team/your GP?",
        blank=True, null=True, max_length=20, choices=Y_N_NA)
    online_information = models.CharField(
        verbose_name="Do you want any online information on post-COVID support?",
        blank=True, null=True, max_length=20, choices=Y_N_NA)

    call_satisfaction         = models.CharField(
        blank=True, null=True, max_length=20, choices=Y_N_NOT_SURE,
        verbose_name="Did you find this call useful?"
    )
    recontact                 = models.NullBooleanField(
        verbose_name="Would you be willing to be contacted again to take part in research?"
    )

    follow_up_outcome         = models.CharField(blank=True, null=True, max_length=50, choices=FOLLOWUP_CHOICES)

    cxr                       = models.NullBooleanField(verbose_name="CXR")
    ecg                       = models.NullBooleanField(verbose_name="ECG")
    echocardiogram            = models.NullBooleanField()
    ct_chest                  = models.NullBooleanField(verbose_name="CT Chest")
    pft                       = models.NullBooleanField(verbose_name="PFT")
    exercise                  = models.NullBooleanField(verbose_name="Exercise Testing")
    repeat_bloods             = models.NullBooleanField()
    other_investigations      = models.CharField(blank=True, null=True, max_length=255)

    anticoagulation            = models.NullBooleanField()
    anticoagulation_gp         = models.NullBooleanField()
    anticoagulation_done       = models.NullBooleanField()
    cardiology                 = models.NullBooleanField()
    cardiology_gp              = models.NullBooleanField()
    cardiology_done            = models.NullBooleanField()
    elderly_care               = models.NullBooleanField()
    elderly_care_gp            = models.NullBooleanField()
    elderly_care_done          = models.NullBooleanField()
    fatigue_services           = models.NullBooleanField()
    fatigue_services_gp        = models.NullBooleanField()
    fatigue_services_done      = models.NullBooleanField()
    hepatology                 = models.NullBooleanField()
    hepatology_gp              = models.NullBooleanField()
    hepatology_done            = models.NullBooleanField()
    neurology                  = models.NullBooleanField()
    neurology_gp               = models.NullBooleanField()
    neurology_done             = models.NullBooleanField()
    primary_care               = models.NullBooleanField()
    primary_care_gp            = models.NullBooleanField()
    primary_care_done          = models.NullBooleanField()
    psychology                 = models.NullBooleanField()
    psychology_gp              = models.NullBooleanField()
    psychology_done            = models.NullBooleanField()
    psychiatry                 = models.NullBooleanField()
    psychiatry_gp              = models.NullBooleanField()
    psychiatry_done            = models.NullBooleanField()
    respiratory                = models.NullBooleanField()
    respiratory_gp             = models.NullBooleanField()
    respiratory_done           = models.NullBooleanField()
    rehabilitation             = models.NullBooleanField()
    rehabilitation_gp          = models.NullBooleanField()
    rehabilitation_done        = models.NullBooleanField()
    other_referral             = models.CharField(blank=True, null=True, max_length=255)
    other_referral_gp          = models.NullBooleanField()
    other_referral_done        = models.NullBooleanField()

    gp_copy                    = models.TextField(
        blank=True, null=True, verbose_name="Copy for clinic letter"
    )
    # the timestamp it was sent to epr, null if it hasn't been.
    sent_to_epr                    = models.DateTimeField(blank=True, null=True)

    def other_symptoms(self):
        symptom_fields = [
            'chest_pain',
            'chest_tightness',
            'myalgia',
            'anosmia',
            'loss_of_taste',
            'chills',
            'anorexia',
            'abdominal_pain',
            'diarrhoea',
            'peripheral_oedema',
            'confusion',
            'focal_weakness'
        ]
        return [self._get_field_title(n) for n in symptom_fields if getattr(self, n)]

    def further_investigations(self):
        investigation_fields =  [
            'cxr',
            'ecg',
            'echocardiogram',
            'ct_chest',
            'pft',
            'exercise',
            'repeat_bloods',
        ]

        investigations = [
            self._get_field_title(n) for n in investigation_fields if getattr(self, n)
        ]
        if self.other_investigations:
            investigations.append(self.other_investigations)

        return investigations

    def referrals(self):
        referred = [
            self._get_field_title(n) for n in self.REFERRAL_FIELDS
            if getattr(self, n) and not getattr(self, '{}_gp'.format(n))
        ]

        if self.other_referral:
            referred.append(self.other_referral)

        return referred

    def gp_referrals(self):
        referred = [
            self._get_field_title(n) for n in self.REFERRAL_FIELDS
            if getattr(self, n) and getattr(self, '{}_gp'.format(n))
        ]
        return referred

    def phq_score(self):
        return calculate_phq_score(self.interest, self.depressed)

    def tsq_score(self):
        return len([i for i in range(1, 11) if getattr(self, 'tsq{}'.format(i))])


class CovidFollowUpCallFollowUpCall(PreviousMRN, EpisodeSubrecord):
    """
    A phone call to a patient seeking follow up on their COVID-19 admission Follow up Call
    """
    _icon = 'fa fa-phone'

    POSITION_CHOICES     = enum('Consultant', 'Registrar', 'Associate Specialist', 'Other')

    class Meta:
        verbose_name = 'Covid Follow Up Subsequent Call'

    when              = models.DateTimeField(blank=True, null=True)
    clinician         = models.CharField(blank=True, null=True, max_length=255) # Default to user
    position          =  models.CharField(
        blank=True, null=True, max_length=255, choices=POSITION_CHOICES)

    bloods            = models.NullBooleanField()
    imaging           = models.NullBooleanField()
    symptoms          = models.NullBooleanField()
    other             = models.CharField(blank=True, null=True, max_length=255)
    echo_results      = models.TextField(blank=True, null=True)

    details           = models.TextField(
        blank=True, null=True, verbose_name="Call Details")

    # the timestamp it was sent to epr, null if it hasn't been.
    sent_to_epr       = models.DateTimeField(blank=True, null=True)

class CovidSixMonthFollowUp(PreviousMRN, EpisodeSubrecord):
    """
    A call made after six months to check on the follow up status of a
    patient.
    """
    _icon = 'fa fa-phone'

    POSITION_CHOICES    = enum('Consultant', 'Registrar', 'Associate Specialist', 'Other')
    YN_DECLINED_CHOICES = enum('Yes', 'No', 'Declined')
    Y_N_NOT_SURE        = enum('Yes', 'No', 'Not sure')
    YN_NA               = enum('Yes', 'No', 'N/A')
    MRC_CHOICES         = enum('1', '2', '3', '4', '5', 'N/A')
    ONE_TO_NINE         = enum('1', '2', '3', '4', '5', '6', '7', '8', '9')
    ZERO_TO_TEN         = enum('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10')
    TREND_CHOICES       = enum('Same', 'Better', 'Worse', 'Back to Baseline')
    LIMITED_BY_CHOICES  = enum('SOB', 'Fatigue', 'Other')
    EXERCISE_CHOICES    = enum('Reduced', 'Back to baseline', 'Unlimited')
    ZERO_TO_THREE       = enum(
        '(0) Not At All',
        '(1) Several days',
        '(2) More than half the days',
        '(3) Nearly every day'
    )

    when               = models.DateTimeField(blank=True, null=True)
    clinician          = models.CharField(blank=True, null=True, max_length=255) # Default to user
    position           = models.CharField(
        blank=True, null=True, max_length=255, choices=POSITION_CHOICES)
    cxr_completed      = models.CharField(
        blank=True, null=True, max_length=255, choices=YN_DECLINED_CHOICES
    )
    bloods_completed   = models.CharField(
        blank=True, null=True, max_length=255, choices=YN_DECLINED_CHOICES
    )
    incomplete_reason  = models.TextField(blank=True, null=True)
    current_breathlessness    = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    max_breathlessness        = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    breathlessness_trend      = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)
    current_cough             = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    max_cough                 = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    cough_trend               = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)
    current_fatigue           = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    max_fatigue               = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    fatigue_trend             = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)
    current_sleep_quality     = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    max_sleep_quality         = models.CharField(
        blank=True, null=True, max_length=5, choices=ZERO_TO_TEN)
    sleep_quality_trend       = models.CharField(
        blank=True, null=True, max_length=40, choices=TREND_CHOICES)

    poor_sleep_noise       = models.NullBooleanField()
    poor_sleep_medications = models.NullBooleanField()
    poor_sleep_other       = models.CharField(max_length=255, blank=True, null=True)

    chest_pain                = models.NullBooleanField(help_text='Chest pain')
    chest_tightness           = models.NullBooleanField(help_text='Chest tightness')
    myalgia                   = models.NullBooleanField()
    confusion                 = models.NullBooleanField(help_text='Confusion or fuzzy head')
    peripheral_oedema         = models.NullBooleanField()
    focal_weakness            = models.NullBooleanField()
    anosmia                   = models.NullBooleanField()
    diarrhoea                 = models.NullBooleanField()
    abdominal_pain            = models.NullBooleanField(verbose_name="Abdominal pain")
    anorexia                  = models.NullBooleanField()

    back_to_normal            = models.NullBooleanField(verbose_name="Do you feel back to normal?")
    why_not_back_to_normal    = models.TextField(blank=True, null=True)
    baseline_health_proximity = models.IntegerField(
        blank=True, null=True, verbose_name="How close to 100% of usual health do you feel?")
    back_to_work              = models.CharField(
        verbose_name="If working, are you back to work?",
        blank=True, null=True, max_length=20, choices=YN_NA)
    current_et                = models.CharField(
        blank=True, null=True, max_length=50,
        choices=EXERCISE_CHOICES,
        verbose_name="Current ET")
    mrc_dyspnoea_scale        = models.CharField(
        blank=True, null=True, max_length=50, choices=MRC_CHOICES,
        verbose_name="MRC Dyspnoea Scale")
    limited_by                = models.CharField(blank=True, null=True,
                                                 max_length=50, choices=LIMITED_BY_CHOICES)
    current_cfs               = models.CharField(
        blank=True, null=True,
        max_length=50, choices=ONE_TO_NINE, verbose_name="Current Clinical Frailty Score")
   # Psychological scores
    interest                  = models.CharField(
        verbose_name="Little interest or pleasure in doing things",
        blank=True, null=True, max_length=50, choices=ZERO_TO_THREE)
    depressed                 = models.CharField(
        verbose_name="Feeling down, depressed or hopeless",
        blank=True, null=True, max_length=50, choices=ZERO_TO_THREE)

    tsq1 = models.NullBooleanField(
        verbose_name='Upsetting thoughts or memories about your hospital admission that have come into your mind against your will'
    )
    tsq2 = models.NullBooleanField(
        verbose_name='Upsetting dreams about the event'
    )
    tsq3 = models.NullBooleanField(
        verbose_name='Acting or feeling as though it is happening again'
    )
    tsq4 = models.NullBooleanField(
        verbose_name='Feeling upset by reminders of the event'
    )
    tsq5 = models.NullBooleanField(
        verbose_name='Bodily reactions such as fast heartbeat, sweatiness, dizziness when reminded of the event'
    )
    tsq6 = models.NullBooleanField(
        verbose_name='Difficulty falling or staying asleep'
    )
    tsq7 = models.NullBooleanField(
        verbose_name='Irritability or bursts of anger'
    )
    tsq8 = models.NullBooleanField(
        verbose_name='Difficulty concentrating'
    )
    tsq9 = models.NullBooleanField(
        verbose_name='Being more aware of potential danger to yourself and others'
    )
    tsq10 = models.NullBooleanField(
        verbose_name='Being jumpy or startled at something unexpected'
    )

    other_concerns = models.TextField(blank=True, null=True)
    call_satisfaction         = models.CharField(
        blank=True, null=True, max_length=20, choices=Y_N_NOT_SURE,
        verbose_name="Did you find this call useful?"
    )
    recontact                 = models.NullBooleanField(
        verbose_name="Would you be willing to be contacted again to take part in research?"
    )

    haem_fu = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient receive haematology/anticoagulation clinic review if needed")
    cardiology_fu = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient receive Cardiology clinic follow up if required?")
    ipat_fu    = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient access self referral to IAPT if received information?")
    smoking_fu  = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient receive smoking cessation input if consented?")
    ct_chest  = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient receive CT chest ?")
    pulmonary_function   = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient receive pulmonary function tests?")
    msk_input     = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient receive MSK input if required?"
    )
    patient_type = models.CharField(
        blank=True, null=True, max_length=250,
        choices=enum('Inpatient', 'Outpatient')
    )
    resp_clinic = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did patient receive a respiratory face to face clinic review if required?"
    )
    calls_post_discharge = models.CharField(
        blank=True, null=True, max_length=250,
        choices=enum('One', 'Two', 'Three', 'Four or more'),
        verbose_name="How many telephone calls did the patient receive after discharge?")

    cxrs = models.CharField(
        blank=True, null=True, max_length=250,
        choices=enum('One', 'Two or more'),
        verbose_name="How many post discharge CXRs did the patient require?")

    online_useful = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did you find the online covid resource information useful?")

    app_useful = models.CharField(
        blank=True, null=True, max_length=250,
        choices=YN_NA,
        verbose_name="Did you find the COVID recovery application useful?")

    gp_copy = models.TextField(
        blank=True, null=True, verbose_name="Copy for clinic letter"
    )

    # the timestamp it was sent to epr, null if it hasn't been.
    sent_to_epr = models.DateTimeField(blank=True, null=True)

    def other_symptoms(self):
        symptom_fields = [
            'chest_pain',
            'chest_tightness',
            'myalgia',
            'anosmia',
            'anorexia',
            'abdominal_pain',
            'diarrhoea',
            'peripheral_oedema',
            'confusion',
            'focal_weakness'
        ]
        return [self._get_field_title(n) for n in symptom_fields if getattr(self, n)]

    def phq_score(self):
        return calculate_phq_score(self.interest, self.depressed)

    def tsq_score(self):
        return len([i for i in range(1, 11) if getattr(self, 'tsq{}'.format(i))])
