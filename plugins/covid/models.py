"""
Models for the Covid plugin
"""
from django.db import models
from opal.core.fields import enum
from opal.models import Patient, PatientSubrecord, EpisodeSubrecord


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


class CovidAdmission(EpisodeSubrecord):
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
        'Rhinitis',
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
        'Respiratory support'
    )

    date_of_admission    = models.DateField(blank=True, null=True)
    date_of_discharge    = models.DateField(blank=True, null=True)

    # Symptoms at admission
    duration_of_symptoms = models.IntegerField(
        blank=True, null=True, verbose_name='Duration In Days At Admissison')
    cough                = models.NullBooleanField()
    shortness_of_breath  = models.NullBooleanField()
    sore_throat          = models.NullBooleanField()
    rhinitis             = models.NullBooleanField()
    fever                = models.NullBooleanField()
    fatigue              = models.NullBooleanField()
    myalgia              = models.NullBooleanField()
    headache             = models.NullBooleanField()
    anorexia             = models.NullBooleanField()
    anosmia              = models.NullBooleanField()
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
    height               = models.CharField(blank=True, null=True, max_length=20, help_text='m')
    weight               = models.CharField(blank=True, null=True, max_length=20, help_text='kg')
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

    smoking_status       = models.CharField(
        blank=True, null=True, max_length=200, choices=SMOKING_CHOICES,
        verbose_name='Smoking Status On Admission'
    )

    # Respiratory support
    maximum_resp_support = models.CharField(
        blank=True, null=True, max_length=200, choices=MAX_RESP_SUPPORT_CHOICES
    )
    max_fio2_non_nc           = models.CharField(blank=True, null=True, max_length=255, help_text='Max FiO2 non NC')
    max_fio2_nc               = models.CharField(blank=True, null=True, max_length=255, help_text='Max FiO2 if NC')
    days_on_cpap              = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On CPAP')
    days_on_niv               = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On NIV')
    days_on_iv                = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On IV')
    days_on_oxygen            = models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On Oxygen')

    final_spo2                = models.CharField(
        blank=True, null=True, max_length=244, verbose_name='Last Available SpO2 Prior To Discharge')
    final_fio2                = models.CharField(
        blank=True, null=True, max_length=244, verbose_name='Last Available FiO2 Prior To Discharge')

    systemic_corticosteroirds = models.NullBooleanField(verbose_name='Treated With Systemic Corticosteroids') # TODO IS THIS HERE?

    covid_code                = models.CharField(blank=True, null=True, max_length=20, choices=COVID_CODE_CHOICES)


class CovidSmokingHistory(EpisodeSubrecord):
    """
    Smoking history
    """
    _icon         = 'fa fa-fire'
    _is_singleton = True

    class Meta:
        verbose_name = 'Smoking History'

    OTHER_SMOKING_CHOICES = enum(
        'Vape',
        'Other drugs'
    )

    pack_year_history = models.TextField(blank=True, null=True)
    vape              = models.NullBooleanField(verbose_name="Vape Smoked")
    other_drugs       = models.NullBooleanField(verbose_name="Other Drugs Smoked")


class CovidSocialHistory(PatientSubrecord):
    _icon         = 'fa fa-users'
    _is_singleton = True

    class Meta:
        verbose_name = 'Social History'

    CIRCUMSTANCES_CHOICES = enum(
        'Independent',
        'Family help',
        'Carers',
        'NH/RH'
    )

    CARER_CHOICES = enum(
        'OD',
        'BD',
        'TDS',
        'QDS'
    )
    SHIELDING_CHOICES = enum(
        'Not',
        'Voluntary Shielding',
        'Extremely Vulnerable',
        'Letter Issued by HCP'
    )

    social_circumstances = models.CharField(
        blank=True, null=True, max_length=200, choices=CIRCUMSTANCES_CHOICES
    )
    carers               = models.CharField(
        blank=True, null=True, max_length=200, choices=CARER_CHOICES
    )
    shielding_status     = models.CharField( # TODO WHAT ARE THESE
        max_length=200, blank=True, null=True, choices=SHIELDING_CHOICES
    )


class LungFunctionTest(EpisodeSubrecord):
    """
    Lung function test results for this patient
    """
    _icon = 'fa fa-crosshairs'

    date    = models.DateField(blank=True, null=True)
    fev1    = models.CharField(blank=True, null=True, max_length=244, verbose_name='FEV1 %')
    fvc     = models.CharField(blank=True, null=True, max_length=244, verbose_name='FVC %')
    lf_dlco = models.CharField(blank=True, null=True, max_length=244, verbose_name='LF DLCO %')


class CovidComorbidities(EpisodeSubrecord):
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


class CovidTrialEnrollment(EpisodeSubrecord):
    """
    Was this patient enrolled on a trial
    """
    _is_singleton = True
    _icon         = 'fa fa-user-md'

    enrolled = models.NullBooleanField()
    details  = models.TextField(blank=True, null=True)


class ITUAdmission(EpisodeSubrecord):
    """
    Details of ITU Admission
    """
    _icon = 'fa fa-heartbeat'

    class Meta:
        verbose_name = 'ITU Admission'

    date_of_admission       = models.DateField(blank=True, null=True)
    apache_score_on_arrival = models.CharField(
        blank=True, null=True, max_length=244, verbose_name='APACHE II score on ITU arrival')
    intubated               = models.NullBooleanField()
    date_of_intubation      = models.DateField(blank=True, null=True)


class CovidCXR(EpisodeSubrecord):
    """
    Covid chest x ray
    """
    _icon = 'fa fa-crosshairs'

    class Meta:
        verbose_name = 'Covid CXR'

    SEVERITY_CHOICES = enum(
        'Mild',
        'Moderate',
        'Severe'
    )

    date = models.DateField(blank=True, null=True)
    covid_code = models.CharField(blank=True, null=True, max_length=20, choices=COVID_CODE_CHOICES)


class CovidCT(EpisodeSubrecord):
    """
    Covid CT Scans
    """
    _icon = 'fa fa-crosshairs'

    class Meta:
        verbose_name = 'Covid CT'

    date   = models.DateField(blank=True, null=True)
    pe     = models.NullBooleanField(verbose_name="Pulmonary Embolism") # WHAT IS THIS? (Pulmonary_embolism)
    report = models.TextField(blank=True, null=True)


class CovidFollowUpCall(EpisodeSubrecord):
    """
    A phone call to a patient seeking follow up on their COVID-19 admission
    """
    _icon = 'fa fa-phone'

    ONE_TO_TEN           = enum('1', '2', '3', '4', '5', '6', '7', '8', '9', '10')
    ONE_TO_NINE          = enum('1', '2', '3', '4', '5', '6', '7', '8', '9')
    ONE_TO_FIVE          = enum('1', '2', '3', '4', '5')
    ZERO_TO_THREE        = (
        ('0', 'Not At All'),
        ('1', 'Several days'),
        ('2', 'More than half the days'),
        ('3', 'Nearly every day')
    )

    POSITION_CHOICES     = enum('Consultant', 'Registrar', 'Associate Specialist', 'Other')
    TREND_CHOICES        = enum('Same', 'Better', 'Worse')
    Y_N_NA               = enum('Yes', 'No', 'N/A')
    LIMITED_BY_CHOICES   = enum('SOB', 'Fatigue', 'Other')
    FOLLOWUP_CHOICES     = enum(
        'Discharge',
        'Repeat CXR and F/U Call',
        'CT Chest',
        'PFTs',
        'Resp OPD',
        'Refer back to Primary Care'
    )

    when               = models.DateTimeField(blank=True, null=True)
    clinician          = models.CharField(blank=True, null=True, max_length=255) # Default to user
    position           = models.CharField(blank=True, null=True, max_length=255, choices=POSITION_CHOICES)
    unreachable        = models.NullBooleanField()
    unable_to_complete = models.NullBooleanField()
    incomplete_reason  = models.TextField(blank=True, null=True)

    smoking_status     = models.CharField(
        blank=True, null=True, max_length=200, choices=SMOKING_CHOICES,
        verbose_name='Smoking staus at follow up'
    )

    changes_to_medication     = models.NullBooleanField(verbose_name="Changes to medication post discharge")
    medication_change_details = models.TextField(blank=True, null=True)

    current_breathlessness    = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_breathlessness        = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    breathlessness_trend      = models.CharField(blank=True, null=True, max_length=10, choices=TREND_CHOICES)
    current_cough             = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_cough                 = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    cough_trend               = models.CharField(blank=True, null=True, max_length=10, choices=TREND_CHOICES)
    current_fatigue           = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_fatigue               = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    fatigue_trend             = models.CharField(blank=True, null=True, max_length=10, choices=TREND_CHOICES)
    current_sleep_quality     = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    max_sleep_quality         = models.CharField(blank=True, null=True, max_length=5, choices=ONE_TO_TEN)
    sleep_quality_trend       = models.CharField(blank=True, null=True, max_length=10, choices=TREND_CHOICES)

    # Symptoms at follow up
    myalgia                   = models.NullBooleanField()
    anosmia                   = models.NullBooleanField()
    anorexia                  = models.NullBooleanField()
    chest_pain                = models.NullBooleanField(help_text='Chest pain')
    chest_tightness           = models.NullBooleanField(help_text='Chest tightness')
    confusion                 = models.NullBooleanField(help_text='Confusion or fuzzy head')
    diarrhoea                 = models.NullBooleanField()
    peripheral_oedema         = models.NullBooleanField()
    abdominal_pain            = models.NullBooleanField()
    focal_weakness            = models.NullBooleanField()
    loss_of_taste             = models.NullBooleanField()

    # Quality of life at follow up
    back_to_normal            = models.NullBooleanField()
    why_not_back_to_normal    = models.TextField(blank=True, null=True)
    baseline_health_proximity = models.IntegerField(
        blank=True, null=True, verbose_name="How close to 100% of usual health do you feel")
    back_to_work              = models.CharField(blank=True, null=True, max_length=20, choices=Y_N_NA)

    current_et                = models.CharField(
        blank=True, null=True, max_length=50, help_text='Metres',
        verbose_name="Current ET") # Exercise tolerance?
    mrc_dyspnoea_scale        = models.CharField(
        blank=True, null=True, max_length=50, choices=ONE_TO_FIVE, verbose_name="MRC Dyspnoea Scale")
    limited_by                = models.CharField(blank=True, null=True,
                                                 max_length=50, choices=LIMITED_BY_CHOICES)
    current_cfs               = models.CharField(
        blank=True, null=True,
        max_length=50, choices=ONE_TO_NINE, verbose_name="Current Clinical Frailty Score")

    # Psychological scores
    interest                  = models.CharField(blank=True, null=True, max_length=50, choices=ZERO_TO_THREE)
    depressed                 = models.CharField(blank=True, null=True, max_length=50, choices=ZERO_TO_THREE)

    psych_referral            = models.NullBooleanField()
    other_concerns            = models.TextField(blank=True, null=True)
    haem_clinic               = models.CharField(blank=True, null=True, max_length=20, choices=Y_N_NA)
    diabetic_team             = models.CharField(blank=True, null=True, max_length=20, choices=Y_N_NA)# TODO What is thsi
    call_satisfaction         = models.CharField(blank=True, null=True, max_length=20, choices=Y_N_NA)
    recontact                 = models.NullBooleanField()
    follow_up_outcome         = models.CharField(blank=True, null=True, max_length=50, choices=FOLLOWUP_CHOICES)
