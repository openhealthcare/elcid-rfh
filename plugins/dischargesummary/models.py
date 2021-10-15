"""
Models for the elCID dischargesummary plugin
"""
from django.db import models
from opal.models import Patient, PatientSubrecord

class PatientDischargeSummaryStatus(PatientSubrecord):
    _is_singleton = True

    has_dischargesummaries = models.BooleanField(default=False)


class DischargeSummary(models.Model):
    """
    """
    # We link the upstream data to our system via a single foreign key to the
    # Patient object. In practice we take the MRN fields and match them
    # with patient.demographics().hospital_number
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='dischargesummaries')
    created_in_elcid        = models.DateTimeField(auto_now_add=True)

    sql_internal_id         = models.IntegerField(blank=True, null=True)
    rf1_number              = models.CharField(blank=True, null=True, max_length=255)
    patient_nhs_number      = models.CharField(blank=True, null=True, max_length=255)
    patient_forenames       = models.CharField(blank=True, null=True, max_length=255)
    patient_surname         = models.CharField(blank=True, null=True, max_length=255)
    patient_dob             = models.DateTimeField(blank=True, null=True)
    date_of_admission       = models.DateTimeField(blank=True, null=True)
    date_of_discharge       = models.DateTimeField(blank=True, null=True)
    last_updated            = models.DateTimeField(blank=True, null=True)
    last_updated_str        = models.CharField(blank=True, null=True, max_length=255)
    ward_name               = models.CharField(blank=True, null=True, max_length=255)
    consultant_name         = models.CharField(blank=True, null=True, max_length=255)
    consultant_department   = models.CharField(blank=True, null=True, max_length=255)
    admission_diagnosis     = models.TextField(blank=True, null=True)
    ae_diagnosis            = models.TextField(blank=True, null=True)
    hsep_problems_diagnosis = models.TextField(blank=True, null=True)
    hsep_actions            = models.TextField(blank=True, null=True)
    other_diagnoses         = models.TextField(blank=True, null=True)
    findings                = models.TextField(blank=True, null=True)
    procedures              = models.TextField(blank=True, null=True)
    investigation_results   = models.TextField(blank=True, null=True)
    management              = models.TextField(blank=True, null=True)
    future_management       = models.TextField(blank=True, null=True)
    allergies               = models.CharField(blank=True, null=True, max_length=255)
    letter_type1            = models.CharField(blank=True, null=True, max_length=255)
    letter_type2            = models.CharField(blank=True, null=True, max_length=255)
    final_letter            = models.CharField(blank=True, null=True, max_length=255)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'SQL_Internal_ID'       : 'sql_internal_id',
        'RF1_NUMBER'            : 'rf1_number',
        'PATIENT_NHS_NUMBER'    : 'patient_nhs_number',
        'PATIENT_FORENAMES'     : 'patient_forenames',
        'PATIENT_SURNAME'       : 'patient_surname',
        'PATIENT_DOB'           : 'patient_dob',
        'DATE_OF_ADMISSION'     : 'date_of_admission',
        'DATE_OF_DISCHARGE'     : 'date_of_discharge',
        'LAST_UPDATED'          : 'last_updated_str',
        'WARD_NAME'             : 'ward_name',
        'CONSULTANT_NAME'       : 'consultant_name',
        'CONSULTANT_DEPARTMENT' : 'consultant_department',
        'ADMISSION_DIAGNOSIS'   : 'admission_diagnosis',
        'AE_Diagnosis'          : 'ae_diagnosis',
        'HSEP_ProblemsDiagnosis': 'hsep_problems_diagnosis',
        'HSEP_Actions'          : 'hsep_actions',
        'OTHER_DIAGNOSES'       : 'other_diagnoses',
        'FINDINGS'              : 'findings',
        'PROCEDURES'            : 'procedures',
        'INVESTIGATION_RESULTS' : 'investigation_results',
        'MANAGEMENT'            : 'management',
        'FUTURE_MANAGEMENT'     : 'future_management',
        'ALLERGIES'             : 'allergies',
        'LETTER_TYPE1'          : 'letter_type1',
        'LETTER_TYPE2'          : 'letter_type2',
        'FINAL_LETTER'          : 'final_letter'
    }

    FIELDS_TO_SERIALIZE = [
        'sql_internal_id',
        'date_of_admission',
        'date_of_discharge',
        'last_updated',
        'ward_name',
        'consultant_name',
        'consultant_department',
        'admission_diagnosis',
        'ae_diagnosis',
        'hsep_problems_diagnosis',
        'hsep_actions',
        'other_diagnoses',
        'findings',
        'procedures',
        'investigation_results',
        'management',
        'future_management',
        'allergies',
        'letter_type1',
        'letter_type2',
        'final_letter',
    ]

    RN_FIELDS = [
        'admission_diagnosis',
        'ae_diagnosis',
        'hsep_problems_diagnosis',
        'hsep_actions',
        'other_diagnoses',
        'findings',
        'procedures',
        'investigation_results',
        'management',
        'future_management',
    ]


    def to_dict(self):
        result = {k: getattr(self, k) for k in self.FIELDS_TO_SERIALIZE}
        result['meds'] = [m.to_dict() for m in self.medications.all()]
        for fname in self.RN_FIELDS:
            if result[fname]:
                result[fname] = result[fname].replace('\r\n', '\n')
        return result


class DischargeMedication(models.Model):
    """
    List of medication known at discharge
    """
    discharge = models.ForeignKey(
        DischargeSummary, on_delete=models.CASCADE, related_name='medications'
    )

    sql_internal_id  = models.IntegerField(blank=True, null=True)
    created_in_elcid = models.DateTimeField(auto_now_add=True)
    tta_main_id      = models.IntegerField(blank=True, null=True)
    last_updated_str = models.CharField(blank=True, null=True, max_length=255)
    last_updated     = models.DateTimeField(blank=True, null=True)
    drug_name        = models.CharField(blank=True, null=True, max_length=255)
    dose             = models.CharField(blank=True, null=True, max_length=255)
    route            = models.CharField(blank=True, null=True, max_length=255)
    frequency        = models.CharField(blank=True, null=True, max_length=255)
    duration         = models.CharField(blank=True, null=True, max_length=255)
    status           = models.CharField(blank=True, null=True, max_length=255)
    status_comments  = models.CharField(blank=True, null=True, max_length=255)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'SQL_Internal_ID': 'sql_internal_id',
        'TTA_Main_ID'    : 'tta_main_id',
        'LAST_UPDATED'   : 'last_updated_str',
        'DRUG_NAME'      : 'drug_name',
        'DOSE'           : 'dose',
        'ROUTE'          : 'route',
        'FREQUENCY'      : 'frequency',
        'DURATION'       : 'duration',
        'STATUS'         : 'status',
        'STATUS_COMMENTS': 'status_comments'
    }

    FIELDS_TO_SERIALIZE = [
        'drug_name',
        'dose',
        'route',
        'frequency',
        'duration',
        'status',
        'status_comments'
    ]


    def to_dict(self):
        return {k: getattr(self, k) for k in self.FIELDS_TO_SERIALIZE}
