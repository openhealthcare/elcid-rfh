"""
Models for the elCID ICU plugin
"""
from django.db import models
from opal.models import Patient, PatientSubrecord

def parse_icu_location(location_string):
    """
    Return a tuple of (hospital, ward, bed) from a location string
    """
    parts = location_string.split('_')
    if len(parts) == 3:
        hospital, ward, bed = parts
    else:
        hospital = None
        ward, bed = parts

    bed = bed.split('-')[1]

    return (hospital, ward, bed)


class ICUWard(models.Model):
    """
    Stores metadata about an ICU ward.

    This is used by the dashboard to show ICU occupancy
    """
    name = models.CharField(blank=True, null=True, max_length=200)
    beds = models.IntegerField(blank=True, null=True)


class ICUHandoverLocation(models.Model):
    """
    Stores the location as entered in the upstream ICU Handover database

    This data is parsed from the upstream integration and is not used
    for the elCID Location panel.
    """
    patient  = models.ForeignKey(Patient, on_delete=models.CASCADE)
    hospital = models.CharField(blank=True, null=True, max_length=200)
    ward     = models.CharField(blank=True, null=True, max_length=200)
    bed      = models.CharField(blank=True, null=True, max_length=200)
    admitted = models.DateField(blank=True, null=True)


class ICUHandover(PatientSubrecord):
    """
    This models mirrors the view we have of the upstream
    ICU handover database on the Freenet application closely.

    This results in some data we will likely never use, and some
    denormalisation.

    We do not rely on the denormalised fields such as name for
    anything other than matching to our patient in elCID on import.
    """
    # Incidental implementation details
    sqlserver_patientmasterfile_uniqueid = models.TextField(blank=True, null=True)
    sqlserver_uniqueid                   = models.TextField(blank=True, null=True)
    sqlserver_insert_datetime            = models.TextField(blank=True, null=True)
    sqlserver_lastupdated_datetime       = models.TextField(blank=True, null=True)
    database_version                     = models.TextField(blank=True, null=True)

    # ICU demographics
    patient_mrn       = models.TextField(blank=True, null=True)
    patient_surname   = models.TextField(blank=True, null=True)
    patient_forename1 = models.TextField(blank=True, null=True)
    patient_height    = models.TextField(blank=True, null=True)
    patient_dob       = models.TextField(blank=True, null=True)
    patient_weight    = models.TextField(blank=True, null=True)

    # ICU Admisssion Metadata
    location                            = models.TextField(blank=True, null=True)
    discharge_date                      = models.TextField(blank=True, null=True)
    discharged                          = models.TextField(blank=True, null=True)
    last_action_performed               = models.TextField(blank=True, null=True)
    referring_consultant                = models.TextField(blank=True, null=True)
    date_itu_admission                  = models.TextField(blank=True, null=True)
    patient_location_prior_to_admission = models.TextField(blank=True, null=True)

    # ICU Admisssion summary
    admission_reason_itu_admission      = models.TextField(blank=True, null=True)
    admission_summary                   = models.TextField(blank=True, null=True)
    admission_history_present_illness   = models.TextField(blank=True, null=True)
    admission_chronic_health_evaluation = models.TextField(blank=True, null=True)
    admission_past_medical_history      = models.TextField(blank=True, null=True)
    admission_regular_medication        = models.TextField(blank=True, null=True)
    admission_allergies                 = models.TextField(blank=True, null=True)
    admission_gcs_score                 = models.TextField(blank=True, null=True)
    admission_gcs_best_motor            = models.TextField(blank=True, null=True)
    admission_gcs_eye_opening           = models.TextField(blank=True, null=True)
    admission_gcs_best_verbal           = models.TextField(blank=True, null=True)

    # ICU Daily status
    dailyprogress_registrars_comments       = models.TextField(blank=True, null=True)
    dailyprogress_consultant_comment        = models.TextField(blank=True, null=True)
    dailyprogress_nurses_handover_comment   = models.TextField(blank=True, null=True)
    dailyprogress_critical_care_mdt         = models.TextField(blank=True, null=True)
    dailyprogress_main_diagnosis            = models.TextField(blank=True, null=True)
    dailyprogress_results_of_investigations = models.TextField(blank=True, null=True)
    dailyprogress_to_do_list                = models.TextField(blank=True, null=True)
    dailyprogress_therapy_input_ot          = models.TextField(blank=True, null=True)
    dailyprogress_therapy_input_pt          = models.TextField(blank=True, null=True)
    dailyprogress_organ_infection           = models.TextField(blank=True, null=True)
    dailyprogress_therapy_input_dietician   = models.TextField(blank=True, null=True)
    dailyprogress_therapy_input_slt         = models.TextField(blank=True, null=True)
    dailyprogress_organ_gi                  = models.TextField(blank=True, null=True)
    dailyprogress_organ_cvs                 = models.TextField(blank=True, null=True)
    dailyprogress_organ_renal               = models.TextField(blank=True, null=True)
    dailyprogress_organ_others              = models.TextField(blank=True, null=True)
    dailyprogress_organ_resp                = models.TextField(blank=True, null=True)
    dailyprogress_organ_cns                 = models.TextField(blank=True, null=True)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'SQLserver_PatientMasterfile_UniqueID'   : 'sqlserver_patientmasterfile_uniqueid',
        'SQLserver_UniqueID'                     : 'sqlserver_uniqueid',
        'SQLserver_Insert_DateTime'              : 'sqlserver_insert_datetime',
        'SQLserver_LastUpdated_DateTime'         : 'sqlserver_lastupdated_datetime',
        'Database_Version'                       : 'database_version',
        'Patient_MRN'                            : 'patient_mrn',
        'Patient_Surname'                        : 'patient_surname',
        'Pateint_Forename1'                      : 'pateint_forename1',
        'Patient_Height'                         : 'patient_height',
        'Patient_DOB'                            : 'patient_dob',
        'Patient_Weight'                         : 'patient_weight',
        'Location'                               : 'location',
        'Discharge_Date'                         : 'discharge_date',
        'Discharged'                             : 'discharged',
        'Last_Action_Performed'                  : 'last_action_performed',
        'Referring_Consultant'                   : 'referring_consultant',
        'Date_ITU_Admission'                     : 'date_itu_admission',
        'Patient_Location_Prior_to_Admission'    : 'patient_location_prior_to_admission',
        'Admission_Reason_ITU_Admission'         : 'admission_reason_itu_admission',
        'Admission_Summary'                      : 'admission_summary',
        'Admission_History_Present_Illness'      : 'admission_history_present_illness',
        'Admission_Chronic_Health_Evaluation'    : 'admission_chronic_health_evaluation',
        'Admission_Past_Medical_History'         : 'admission_past_medical_history',
        'Admission_Regular_Medication'           : 'admission_regular_medication',
        'Admission_Allergies'                    : 'admission_allergies',
        'Admission_GCS_Score'                    : 'admission_gcs_score',
        'Admission_GCS_Best_Motor'               : 'admission_gcs_best_motor',
        'Admission_GCS_Eye_Opening'              : 'admission_gcs_eye_opening',
        'Admission_GCS_Best_Verbal'              : 'admission_gcs_best_verbal',
        'DailyProgress_Registrars_Comments'      : 'dailyprogress_registrars_comments',
        'DailyProgress_Consultant_Comment'       : 'dailyprogress_consultant_comment',
        'DailyProgress_Nurses_Handover_Comment'  : 'dailyprogress_nurses_handover_comment',
        'DailyProgress_Critical_Care_MDT'        : 'dailyprogress_critical_care_mdt',
        'DailyProgress_Main_Diagnosis'           : 'dailyprogress_main_diagnosis',
        'DailyProgress_Results_of_Investigations': 'dailyprogress_results_of_investigations',
        'DailyProgress_To_Do_List'               : 'dailyprogress_to_do_list',
        'DailyProgress_Therapy_Input_OT'         : 'dailyprogress_therapy_input_ot',
        'DailyProgress_Therapy_Input_PT'         : 'dailyprogress_therapy_input_pt',
        'DailyProgress_Organ_Infection'          : 'dailyprogress_organ_infection',
        'DailyProgress_Therapy_Input_Dietician'  : 'dailyprogress_therapy_input_dietician',
        'DailyProgress_Therapy_Input_SLT'        : 'dailyprogress_therapy_input_slt',
        'DailyProgress_Organ_GI'                 : 'dailyprogress_organ_gi',
        'DailyProgress_Organ_CVS'                : 'dailyprogress_organ_cvs',
        'DailyProgress_Organ_Renal'              : 'dailyprogress_organ_renal',
        'DailyProgress_Organ_Others'             : 'dailyprogress_organ_others',
        'DailyProgress_Organ_Resp'               : 'dailyprogress_organ_resp',
        'DailyProgress_Organ_CNS'                : 'dailyprogress_organ_cns',
    }
