"""
Models for the elCID Handover plugin
"""
from django.db import models
from opal.models import Patient, PatientSubrecord


class PatientAMTHandoverStatus(PatientSubrecord):
    _is_singleton = True

    has_handover = models.BooleanField(default=False)


class AMTHandover(models.Model):
    """
    This model mirrors the upstream Freenet AMT handover database.
    We import data from a View that cleans the raw table used for
    generic handover databases to be AMT specific.

    We store data here as closely as possible to the format we
    see in that view, even though we do not use all of it at this time.

    We do not rely on denormalised demographic fields such as name  etc
    beyond initial matching to our patient in elCID on import using MRN.
    """
    # We link the upstream data to our system via a single foreign key to the
    # Patient object. In practice we take the MRN fields and match them
    # with patient.demographics().hospital_number
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='amt_handover')

    # SQL Database Table unique ID (Primary Key)
    sqlserver_id                   = models.IntegerField()
    # Date Episode saved to SQL System Generated
    sqlserver_insert_datetime      = models.DateTimeField(blank=True, null=True)
    # DateTime SQL database last modified
    sqlserver_lastupdated_datetime = models.DateTimeField(blank=True, null=True)
    # 689966 = Test; 689967 = Live
    handover_version = models.IntegerField()

    # From Cerner
    mrn              = models.CharField(max_length=255, blank=True, null=True)
    nhs_number       = models.CharField(max_length=255, blank=True, null=True)
    patient_surname  = models.CharField(max_length=255, blank=True, null=True)
    patient_forename = models.CharField(max_length=255, blank=True, null=True)
    patient_dob      = models.CharField(max_length=255, blank=True, null=True)
    contact_number   = models.CharField(max_length=255, blank=True, null=True)

    # Link to Cerner Encounter
    cerner_visit_id = models.CharField(max_length=255, blank=True, null=True)

    # Always AMT
    speciality  = models.CharField(max_length=255, blank=True, null=True)
    # UserID last updated
    update_user = models.CharField(max_length=255, blank=True, null=True)

    # Discharged from Database Y/N
    discharged = models.CharField(max_length=10, blank=True, null=True)
    # Referred / Reviewed / Clerked / PTWR Seen (Post Take Ward Round)
    status     = models.CharField(max_length=100, blank=True, null=True)
    # Non-Covid / Covid (suspected/confirmed)
    rota       = models.CharField(max_length=100, blank=True, null=True)
    # Dropdown list From Cerner or
    # TCI – To Come In
    # RAT – Rapid Access Triage
    # RESUS – Resusitation
    # ATA – Adult treatment area
    # AAU – Adult asessment unit
    # ACU – Ambulatory care unit
    # AAL – Acute Assessment Lounge
    # UCC – Urgent Care Centre
    # Will be corrected if Encounter Linked
    actual_location      = models.CharField(max_length=100, blank=True, null=True)
    bed_number           = models.CharField(max_length=100, blank=True, null=True)
    # Dropdown List
    planned_location     = models.CharField(max_length=255, blank=True, null=True)
    referral_added       = models.DateTimeField(blank=True, null=True)
    # GP / ED / IP / Other
    referral_source      = models.CharField(max_length=255, blank=True, null=True)
    # Freetext if Other Selected
    referral_other       = models.CharField(max_length=255, blank=True, null=True)
    # Pulled from User ID details
    referral_user        = models.CharField(max_length=255, blank=True, null=True)
    # Freetext diagnosis
    presenting_complaint = models.CharField(max_length=16000, blank=True, null=True)
    # HSEP / TREAT / Surgical / All Other Specialities
    team                 = models.CharField(max_length=100, blank=True, null=True)
    # Day / Night take
    shift                = models.CharField(max_length=100, blank=True, null=True)
    review_datetime      = models.DateTimeField(blank=True, null=True)
    # DropDown List
    to_be_clerked_by     = models.CharField(max_length=255, blank=True, null=True)
    # Freetext if Other Selected
    to_be_clerked_by_other = models.CharField(max_length=255, blank=True, null=True)
    # DropDown List
    clerked_by           = models.CharField(max_length=255, blank=True, null=True)
    # Freetext if Other Selected
    clerked_by_other     = models.CharField(max_length=255, blank=True, null=True)
    clerked_datetime     = models.DateTimeField(blank=True, null=True)
    ptwr_datetime        = models.DateTimeField(blank=True, null=True)
    # DropDown List
    ptwr_consultant      = models.CharField(max_length=255, blank=True, null=True)
    consultant_diagnosis = models.CharField(max_length=16000, blank=True, null=True)
    management_plan      = models.CharField(max_length=16000, blank=True, null=True)
    outcome              = models.CharField(max_length=16000, blank=True, null=True)
    # DropDown List
    discharge_destination = models.CharField(max_length=255, blank=True, null=True)
    outcome_datetime      = models.DateTimeField(blank=True, null=True)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'id'                        : 'sqlserver_id',
        'Version'                   : 'handover_version',
        'specialty'                 : 'specialty',
        'SQL_Insert_Date'           : 'sqlserver_insert_datetime',
        'SQL_Last_Updated'          : 'sqlserver_lastupdated_datetime',
        'Discharged'                : 'discharged',
        'UserID'                    : 'update_user',
        'MRN'                       : 'mrn',
        'nhs_number'                : 'nhs_number',
        'patient_surname'           : 'patient_surname',
        'patient_forename'          : 'patient_forename',
        'patient_dob'               : 'patient_dob',
        'Status'                    : 'status',
        'Rota'                      : 'rota',
        'Actual_Location'           : 'actual_location',
        'BedNo'                     : 'bed_number',
        'Planned_Location'          : 'planned_location',
        'Cerner_VisitID'            : 'cerner_visit_id',
        'Date_Referral_Added'       : 'referral_added',
        'Presenting_Complaint'      : 'presenting_complaint',
        'Team'                      : 'team',
        'Shift'                     : 'shift',
        'Referral_Source'           : 'referral_source',
        'Referral_Source_Freetext'  : 'referral_other',
        'Referral_Entered_By'       : 'referral_user',
        'Date_Reviewed'             : 'review_datetime',
        'To_be_Clerked_By'          : 'to_be_clerked_by',
        'To_be_Clerked_by_Freetext' : 'to_be_clerked_by_other',
        'Clerked_By'                : 'clerked_by',
        'Date_Clerked'              : 'clerked_datetime',
        'Clerked_By_Name_Freetext'  : 'clerked_by_other',
        'Contact_Number'            : 'contact_number',
        'Date_PTWR_Consultant_Seen' : 'ptwr_datetime',
        'PTWR_Consultant_Seen'      : 'ptwr_consultant',
        'Consultant_Final_diagnosis': 'consultant_diagnosis',
        'Management_Plan'           : 'management_plan',
        'Outcome'                   : 'outcome',
        'Discharge_Destination'     : 'discharge_destination',
        'Outcome_Date'              : 'outcome_datetime'
    }

    FIELDS_TO_SERIALIZE = [
        'discharged',
        'update_user',
        'status',
        'rota',
        'actual_location',
        'bed_number',
        'planned_location',
        'cerner_visit_id',
        'referral_added',
        'presenting_complaint',
        'team',
        'shift',
        'referral_source',
        'referral_other',
        'referral_user',
        'review_datetime',
        'clerked_by',
        'clerked_datetime',
        'clerked_by_other',
        'contact_number',
        'ptwr_datetime',
        'ptwr_consultant',
        'consultant_diagnosis',
        'management_plan',
        'outcome',
        'discharge_destination',
        'outcome_datetime'
    ]

    def to_dict(self):
        dicted = {k: getattr(self, k) for k in self.FIELDS_TO_SERIALIZE}
        return dicted


class PatientNursingHandoverStatus(PatientSubrecord):
    _is_singleton = True

    has_handover = models.BooleanField(default=False)


class NursingHandover(models.Model):
    """
    This model mirrors the upstream Freenet Nursing handover database.

    We import data from a view that cleans the raw table(s) used.

    We store the data here as closely as possible even though we do not
    use all of it at this time.

    The denormalised demographic data is here for audit puroposes only -
    we match on the MRN field to our elCID record and display all
    demographics from there.
    """
    # We link the upstream data to our system via a single foreign key to the
    # Patient object. In practice we take the MRN fields and match them
    # with patient.demographics().hospital_number
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='nursing_handover')
    # As the upstream data is a view filtered on ative, we don't gert any record
    # of when a patient is removed from the nursing handover.
    # We add our own flag to enable a current nursing handover mirror while
    # retaining the previous entries.
    active = models.BooleanField(default=True)

    sqlserver_uniqueid             = models.IntegerField()
    database_version               = models.IntegerField()

    os_user                        = models.CharField(max_length=255, blank=True, null=True)
    handover_list_code             = models.CharField(max_length=255, blank=True, null=True)
    handover_list_desc             = models.CharField(max_length=255, blank=True, null=True)

    sqlserver_insert_datetime      = models.DateTimeField(blank=True, null=True)
    sqlserver_lastupdated_datetime = models.DateTimeField(blank=True, null=True)

    patient_mrn                    = models.CharField(max_length=255, blank=True, null=True)
    patient_surname                = models.CharField(max_length=255, blank=True, null=True)
    patient_forename               = models.CharField(max_length=255, blank=True, null=True)
    patient_dob                    = models.CharField(max_length=255, blank=True, null=True)

    ward_code                      = models.CharField(max_length=255, blank=True, null=True)
    bedno                          = models.CharField(max_length=255, blank=True, null=True)

    consultant_code                = models.CharField(max_length=255, blank=True, null=True)
    diagnosis                      = models.CharField(max_length=16000, blank=True, null=True)
    clinical_instructions          = models.CharField(max_length=16000, blank=True, null=True)
    results_to_be_reviewed         = models.CharField(max_length=16000, blank=True, null=True)

    therapy_input_date             = models.DateTimeField(blank=True, null=True)
    therapy_input_dietician        = models.CharField(max_length=16000, blank=True, null=True)
    therapy_input_ot               = models.CharField(max_length=16000, blank=True, null=True)
    therapy_input_pt               = models.CharField(max_length=16000, blank=True, null=True)
    therapy_input_slt              = models.CharField(max_length=16000, blank=True, null=True)
    therapy_input_neuro            = models.CharField(max_length=16000, blank=True, null=True)
    pharmacy_input                 = models.CharField(max_length=16000, blank=True, null=True)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'SQLserver_UniqueID'            : 'sqlserver_uniqueid',
        'Database_Version'              : 'database_version',
        'os_user'                       : 'os_user',
        'Handover_List_Code'            : 'handover_list_code',
        'Handover_List_Desc'            : 'handover_list_desc',
        'SQLserver_Insert_DateTime'     : 'sqlserver_insert_datetime',
        'SQLserver_LastUpdated_DateTime': 'sqlserver_lastupdated_datetime',
        'Patient_MRN'                   : 'patient_mrn',
        'patient_surname'               : 'patient_surname',
        'patient_forename'              : 'patient_forename',
        'patient_dob'                   : 'patient_dob',
        'Ward_Code'                     : 'ward_code',
        'bedno'                         : 'bedno',
        'consultant_Code'               : 'consultant_code',
        'diagnosis'                     : 'diagnosis',
        'clinical_instructions'         : 'clinical_instructions',
        'results_to_be_reviewed'        : 'results_to_be_reviewed',
        'Therapy_Input_Date'            : 'therapy_input_date',
        'Therapy_Input_Dietician'       : 'therapy_input_dietician',
        'Therapy_Input_OT'              : 'therapy_input_ot',
        'Therapy_Input_PT'              : 'therapy_input_pt',
        'Therapy_Input_SLT'             : 'therapy_input_slt',
        'Therapy_Input_Neuro'           : 'therapy_input_neuro',
        'Pharmacy_Input'                : 'pharmacy_input'
    }

    FIELDS_TO_SERIALIZE = [
        'sqlserver_uniqueid',
        'database_version',
        'os_user',
        'handover_list_code',
        'handover_list_desc',
        'sqlserver_insert_datetime',
        'sqlserver_lastupdated_datetime',
        'patient_mrn',
        'patient_surname',
        'patient_forename',
        'patient_dob',
        'ward_code',
        'bedno',
        'consultant_code',
        'diagnosis',
        'clinical_instructions',
        'results_to_be_reviewed',
        'therapy_input_date',
        'therapy_input_dietician',
        'therapy_input_ot',
        'therapy_input_pt',
        'therapy_input_slt',
        'therapy_input_neuro',
        'pharmacy_input'
    ]

    def to_dict(self):
        dicted = {k: getattr(self, k) for k in self.FIELDS_TO_SERIALIZE}
        return dicted
