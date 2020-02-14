"""
Models for the elCID appointment plugin
"""
from django.db import models
from opal.models import Patient


class Appointment(models.Model):
    """
    An (Outpatient) appointment at the hospital.

    These are defined in the Cerner appointment application, transmitted
    via HL7 messages to an RFH IT database, which we poll to populate this
    table.

    Here, we replicate that view directly, even though we don't currently
    use all the fields.

    Our table becomes a filtered subset of the upstream database.
    """
    # We link the upstream data to our system via a single foreign key to the
    # Patient object. In practice we take the MRN fields and match them
    # with patient.demographics().hospital_number
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')

    # The upstream demographics in this view are denormalised here to aid
    # debugging by mirroring the upstream View. We do not intend to use
    # these fields in our application.
    v_patient_number     = models.CharField(max_length=255, blank=True, null=True, help_text="MRN")
    v_patient_nhs_number = models.CharField(max_length=255, blank=True, null=True)
    v_patient_surname    = models.CharField(max_length=255, blank=True, null=True)
    v_patient_forename   = models.CharField(max_length=255, blank=True, null=True)
    v_patient_dob        = models.DateTimeField(blank=True, null=True)
    patient_number       = models.CharField(max_length=255, blank=True, null=True, help_text="MRN")

    # The next set of fields describe the 'Encounter'. In practice we ignore
    # these in our application as they are not usefully filled in as far as our
    # patient cohort is concerned.
    v_patient_class         = models.CharField(max_length=255, blank=True, null=True,
                                               help_text="Encounter Patient Class")
    v_attending_doctor_code = models.CharField(max_length=255, blank=True, null=True,
                                               help_text="Encounter consultant")
    v_attending_doctor_name = models.CharField(max_length=255, blank=True, null=True,
                                               help_text="Encounter consultant")
    v_referring_doctor_code = models.CharField(max_length=255, blank=True, null=True,
                                               help_text="Encounter referring doctor")
    v_referring_doctor_name = models.CharField(max_length=255, blank=True, null=True,
                                               help_text="Encounter referring doctor")
    v_patient_type          = models.CharField(max_length=255, blank=True, null=True,
                                               help_text="Encounter Patient Type")
    v_account_status        = models.CharField(max_length=255, blank=True, null=True)

    # The next group of fields describe the originating HL7 message for traceability
    # and debugging purposes.
    hl7_message_type = models.CharField(max_length=255, blank=True, null=True,
                                        help_text="Appointment HL7 message type")
    hl7_message_date = models.DateTimeField(blank=True, null=True,
                                            help_text="Appointment HL7 Date")
    hl7_message_id   = models.CharField(max_length=255, blank=True, null=True,
                                        help_text="Appointment HL7 ID")

    # Then some fields that relate to implementation details of the middleman database.
    sqlserver_id = models.IntegerField(blank=True, null=True,
                                       help_text="Internal SQL Appointment Primary Key")
    insert_date  = models.DateTimeField(blank=True, null=True,
                                        help_text="Datetime inserted into the database")
    last_updated = models.DateTimeField(blank=True, null=True,
                                        help_text="Datetime last updated on the database")

    # These "AIG" fields describe the staff member and location.
    # For the clinics we are concerned with, these are rarely, if ever accurate.
    aig_resource_id          = models.CharField(
        max_length=255,blank=True, null=True,
        help_text="General Resourse associated with non-consultant seeing the patient eg SPR, Nurse, Therapist")
    aiL_location_resource_id = models.CharField(max_length=255,blank=True, null=True,
                                                help_text="Actual location of the appointment")
    aip_personnel_id         = models.CharField(max_length=255, blank=True, null=True,
                                                help_text="Consultant resource details if they are seeing the patient.")

    # It is entirely ambiguous what these "TCI" fields refer to
    tci_datetime_text = models.CharField(max_length=255, blank=True, null=True)
    tci_datetime      = models.DateTimeField(blank=True, null=True)
    tci_location      = models.CharField(max_length=255, blank=True, null=True)

    # Finally we discover some fields that describe an appointment
    encounter_number       = models.CharField(max_length=255, blank=True, null=True)
    visit_id               = models.CharField(max_length=255, blank=True, null=True)
    appointment_id         = models.CharField(max_length=255, blank=True, null=True,
                                              help_text="Unique appointment identifier")
    filler_appointment_id  = models.CharField(max_length=255, blank=True, null=True,
                                              help_text="Choose & Book ID when relevent")
    full_appointment_type  = models.CharField(max_length=255, blank=True, null=True,
                                              help_text="Raw Appointment Type")
    duration               = models.CharField(max_length=255, blank=True, null=True)
    duration_units         = models.CharField(max_length=255, blank=True, null=True)
    start_datetime         = models.DateTimeField(blank=True, null=True)
    end_datetime           = models.DateTimeField(blank=True, null=True)
    full_contact_person    = models.CharField(max_length=255,blank=True, null=True)
    full_entered_by_person = models.CharField(max_length=255,blank=True, null=True)
    status_code            = models.CharField(max_length=255, blank=True, null=True)
    hospital_service       = models.CharField(max_length=255, blank=True, null=True,
                                              help_text="Speciality code associated with the encounter")

    # These fields are 'derived' - by which we interpret that the middleman database has
    # done some processing on the raw HL7 text
    derived_appointment_type          = models.CharField(max_length=100, blank=True, null=True,
                                                         help_text="Cleaned up Appointment type (Taken from Full Appointment type)")
    derived_appointment_location      = models.CharField(max_length=255, blank=True, null=True,
                                                         help_text="Cleaned up Appointment location (taken from AIL)")
    derived_appointment_location_site = models.CharField(max_length=255, blank=True, null=True,
                                                         help_text="Cleaned up Appointment location Site (taken from AIL)")
    derived_clinic_resource           = models.CharField(max_length=255, blank=True, null=True,
                                                         help_text="Cleaned up Resource (taken from AIL & AIP) AIP taken presedence")

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'vPatient_Number'                  : 'v_patient_number',
        'vPatient_NHS_Number'              : 'v_patient_nhs_number',
        'vPatient_Surname'                 : 'v_patient_surname',
        'vPatient_Forename'                : 'v_patient_forename',
        'vPatient_DOB'                     : 'v_patient_dob',
        'Patient_Number'                   : 'patient_number',
        'vPatient_Class'                   : 'v_patient_class',
        'vAttending_Doctor_Code'           : 'v_attending_doctor_code',
        'vAttending_Doctor_Name'           : 'v_attending_doctor_name',
        'vReferring_Doctor_Code'           : 'v_referring_doctor_code',
        'vReferring_Doctor_Name'           : 'v_referring_doctor_name',
        'vPatient_Type'                    : 'v_patient_type',
        'vAccount_Status'                  : 'v_account_status',
        'HL7_Message_Type'                 : 'hl7_message_type',
        'HL7_Message_Date'                 : 'hl7_message_date',
        'HL7_Message_ID'                   : 'hl7_message_id',
        'id'                               : 'sqlserver_id',
        'insert_date'                      : 'insert_date',
        'last_updated'                     : 'last_updated',
        'AIG_Resource_ID'                  : 'aig_resource_id',
        'AIL_Location_Resource_ID'         : 'ail_location_resource_id',
        'AIP_Personnel_ID'                 : 'aip_personnel_id',
        'TCI_DateTime_Text'                : 'tci_datetime_text',
        'TCI_DateTime'                     : 'tci_datetime',
        'TCI_Location'                     : 'tci_location',
        'Encounter_Number'                 : 'encounter_number',
        'Visit_ID'                         : 'visit_id',
        'Appointment_ID'                   : 'appointment_id',
        'Filler_Appointment_ID'            : 'filler_appointment_id',
        'Full_Appointment_Type'            : 'full_appointment_type',
        'Appointment_Duration'             : 'duration',
        'Appointment_Duration_Units'       : 'duration_units',
        'Appointment_Start_Datetime'       : 'start_datetime',
        'Appointment_End_Datetime'         : 'end_datetime',
        'Full_Contact_Person'              : 'full_contact_person',
        'Full_Entered_by_Person'           : 'full_entered_by_person',
        'Appointment_Status_Code'          : 'status_code',
        'Hospital_Service'                 : 'hospital_service',
        'Derived_Appointment_Type'         : 'derived_appointment_type',
        'Derived_Appointment_Location'     : 'derived_appointment_location',
        'Derived_Appointment_Location_Site': 'derived_appointment_location_site',
        'derived_clinic_resource'          : 'derived_clinic_resource'
    }
