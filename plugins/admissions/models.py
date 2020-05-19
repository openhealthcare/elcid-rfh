"""
Models for the elCID admissions plugin
"""
from django.db import models
from opal.models import Patient, PatientSubrecord

from plugins.admissions import constants


class PatientEncounterStatus(PatientSubrecord):
    _is_singleton = True

    has_encounters = models.BooleanField(default=False)


class Encounter(models.Model):
    """
    An Encounter at the hospital as defined by Cerner / ADT

    These are transmitted as HL7 messages and then stored in an RFH
    SQL database which we poll to populate this table.

    Here we replicate that database table closely, even though we don't
    currently use all fields.

    Our table should be the equivalent of the upstream table, filtered
    to only inlcude our elCID cohort.
    """
    # We link the upstream data to our system via a single foreign key to the
    # Patient object. In practice we take the MRN fields and match them
    # with patient.demographics().hospital_number
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='encounters')

    # Note: Field - level comments here are from the documentation provided by the integration team
    upstream_id                        = models.IntegerField(blank=True, null=True)              # Internal SQL Database identifier - Primary Key
    msh_7                              = models.DateTimeField(blank=True, null=True)             # HL7 Message Datetime sent from Cerner
    msh_9_msg_type                     = models.CharField(blank=True, null=True, max_length=4)   # Last HL7 Message update Type
    evn_2_movement_date                = models.DateTimeField(blank=True, null=True)             # Cerner Event Datetime
    pid_3_mrn                          = models.CharField(blank=True, null=True, max_length=255) # Patient Hospital Number
    pid_3_nhs                          = models.CharField(blank=True, null=True, max_length=255) # Patient NHS Number
    pid_18_account_number              = models.CharField(blank=True, null=True, max_length=25)  # Encounter ID
    pv1_2_patient_class                = models.CharField(blank=True, null=True, max_length=50)
    pv1_3_hospital                     = models.CharField(blank=True, null=True, max_length=50)  # Cerner Facility - Not very usefull
    pv1_3_ward                         = models.CharField(blank=True, null=True, max_length=50)  # Location
    pv1_3_room                         = models.CharField(blank=True, null=True, max_length=50)
    pv1_3_bed                          = models.CharField(blank=True, null=True, max_length=50)
    pv1_3_ambulatory_indicator         = models.CharField(blank=True, null=True, max_length=50)
    pv1_3_building                     = models.CharField(blank=True, null=True, max_length=50)  # Cerner building - much better for identifying by site
    pv1_4_admission_type               = models.CharField(blank=True, null=True, max_length=50)
    pv1_6_hospital                     = models.CharField(blank=True, null=True, max_length=50)  # Previous Facility
    pv1_6_ward                         = models.CharField(blank=True, null=True, max_length=50)  # Previous Location
    pv1_6_room                         = models.CharField(blank=True, null=True, max_length=50)  # Previous Room
    pv1_6_bed                          = models.CharField(blank=True, null=True, max_length=50)  # Previous Bed
    pv1_7_consultant_code              = models.CharField(blank=True, null=True, max_length=50)  # Encounter clinician NACS code
    consultant_name                    = models.CharField(blank=True, null=True, max_length=50)  # Encounter clinician name
    # Encounter Speciality code
    # 3 digit = National speciality
    # 5 digit = local Treat function where 1st 3 digits in the parent national speciality code
    pv1_10_speciality_code             = models.CharField(blank=True, null=True, max_length=50)
    speciality_name                    = models.CharField(blank=True, null=True, max_length=50)  # Encounter Speciality Description
    pv1_14_admission_source            = models.CharField(blank=True, null=True, max_length=50)
    pv1_18_visit_patient_type_original = models.CharField(blank=True, null=True, max_length=50)
    pv1_18_visit_patient_type_product  = models.CharField(blank=True, null=True, max_length=50)
    pv1_19_hsn                         = models.CharField(blank=True, null=True, max_length=50)  # Cerner Encounter Visit ID
    pv1_41_account_status              = models.CharField(blank=True, null=True, max_length=50)
    pd1_3_practice_code                = models.CharField(blank=True, null=True, max_length=50)  # Registered GP Practice Code
    pd1_4_national_code                = models.CharField(blank=True, null=True, max_length=50)  # Registered GP National Code
    pv1_44_admit_date_time             = models.DateTimeField(blank=True, null=True)             # Cerner Encounter Admission Datetime
    pv1_45_discharge_date_time         = models.DateTimeField(blank=True, null=True)             # Cerner Encounter Discharge Datetime
    pv2_2_patient_type                 = models.CharField(blank=True, null=True, max_length=50)
    fin_hsn                            = models.CharField(blank=True, null=True, max_length=50)
    last_updated                       = models.DateTimeField(blank=True, null=True)             # SQL database update timestamp
    insert_date                        = models.DateTimeField(blank=True, null=True)             # SQL database insert timestamp
    parent_mrn                         = models.CharField(blank=True, null=True, max_length=20)  # MRN of parent record following a Cerner Merge
    comments                           = models.TextField(blank=True, null=True)                 # Comments explaining that the patient was merged

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'ID'                                : 'upstream_id',
        'MSH_7'                             : 'msh_7',
        'MSH_9_MSG_TYPE'                    : 'msh_9_msg_type',
        'EVN_2_MOVEMENT_DATE'               : 'evn_2_movement_date',
        'PID_3_MRN'                         : 'pid_3_mrn',
        'PID_3_NHS'                         : 'pid_3_nhs',
        'PID_18_ACCOUNT_NUMBER'             : 'pid_18_account_number',
        'PV1_2_PATIENT_CLASS'               : 'pv1_2_patient_class',
        'PV1_3_HOSPITAL'                    : 'pv1_3_hospital',
        'PV1_3_WARD'                        : 'pv1_3_ward',
        'PV1_3_ROOM'                        : 'pv1_3_room',
        'PV1_3_BED'                         : 'pv1_3_bed',
        'PV1_3_AMBULATORY_INDICATOR'        : 'pv1_3_ambulatory_indicator',
        'PV1_3_BUILDING'                    : 'pv1_3_building',

        # WHAT ARE THESE CODES?
        'PV1_4_ADMISSION_TYPE'              : 'pv1_4_admission_type',

        'PV1_6_HOSPITAL'                    : 'pv1_6_hospital',
        'PV1_6_WARD'                        : 'pv1_6_ward',
        'PV1_6_ROOM'                        : 'pv1_6_room',
        'PV1_6_BED'                         : 'pv1_6_bed',
        'PV1_7_CONSULTANT_CODE'             : 'pv1_7_consultant_code',
        'CONSULTANT_NAME'                   : 'consultant_name',
        'PV1_10_SPECIALITY_CODE'            : 'pv1_10_speciality_code',
        'SPECIALITY_NAME'                   : 'speciality_name',

        # WHAT ARE THESE CODES?
        'PV1_14_ADMISSION_SOURCE'           : 'pv1_14_admission_source',

        'PV1_18_VISIT_PATIENT_TYPE_ORIGINAL': 'pv1_18_visit_patient_type_original',
        'PV1_18_VISIT_PATIENT_TYPE_PRODUCT' : 'pv1_18_visit_patient_type_product',
        'PV1_19_HSN'                        : 'pv1_19_hsn',
        'PV1_41_ACCOUNT_STATUS'             : 'pv1_41_account_status',
        'PD1_3_PRACTICE_CODE'               : 'pd1_3_practice_code',
        'PD1_4_NATIONAL_CODE'               : 'pd1_4_national_code',
        'PV1_44_ADMIT_DATE_TIME'            : 'pv1_44_admit_date_time',
        'PV1_45_DISCHARGE_DATE_TIME'        : 'pv1_45_discharge_date_time',
        'PV2_2_PATIENT_TYPE'                : 'pv2_2_patient_type',
        'FIN_HSN'                           : 'fin_hsn',
        'LAST_UPDATED'                      : 'last_updated',
        'INSERT_DATE'                       : 'insert_date',
        'PARENT_MRN'                        : 'parent_mrn',
        'COMMENTS'                          : 'comments',
    }

    # Although we maintain the upstream column names with minimal alterations,
    # there is no real utility in sending metadata about the original HL7v2 message
    # ADT format fieldnames through to the front end and using them in templates.
    #
    # Accdcordingly we re-name the fields that we will serialise via the API to
    # more usable properties to be rendered in templates
    FIELDS_TO_SERIALIZE = {
        'evn_2_movement_date'       : 'movement_date',
        'pv1_2_patient_class'       : 'patient_class',
        'pv1_3_ward'                : 'ward',
        'pv1_3_room'                : 'room',
        'pv1_3_bed'                 : 'bed',
        'consultant_name'           : 'consultant_name',
        'speciality_name'           : 'speciality_name',
        'pv1_44_admit_date_time'    : 'admit_datetime',
        'pv1_45_discharge_date_time': 'discharge_datetime',
        'pv1_3_ambulatory_indicator': 'ambulatory_indicator',
    }

    def to_dict(self):
        """
        Serialise an encounter instance for use on the client
        """
        serialized =  {
            dictfield: getattr(self, modelfield)
            for modelfield, dictfield in self.FIELDS_TO_SERIALIZE.items()
        }

        if self.msh_9_msg_type:
            serialized['last_update_type'] = constants.MESSAGE_CODES[self.msh_9_msg_type]

        serialized['hospital'] = constants.BUILDING_CODES.get(self.pv1_3_building)

        return serialized
