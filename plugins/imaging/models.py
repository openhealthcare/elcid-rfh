"""
Models for the elCID imaging plugin
"""
from django.db import models
from opal.models import Patient, PatientSubrecord


class PatientImagingStatus(PatientSubrecord):
    _is_singleton = True

    has_imaging = models.BooleanField(default=False)


class Imaging(models.Model):
    """
    Imaging reports from the PACS system.
    """
    # We link the upstream data to our system via a single foreign key to the
    # Patient object. In practice we take the MRN fields and match them
    # with patient.demographics().hospital_number
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='imaging')

    sql_id               = models.IntegerField(blank=True, null=True) # Internal SQL record ID
    patient_number       = models.CharField(blank=True, null=True, max_length=255)
    patient_surname      = models.CharField(blank=True, null=True, max_length=255)
    patient_forename     = models.CharField(blank=True, null=True, max_length=255)
    # CRIS report identifer
    result_id            = models.CharField(blank=True, null=True, max_length=255)
    # Cerner Initial Order ID
    order_number         = models.CharField(blank=True, null=True, max_length=255)
    # Date requested
    order_effective_date = models.DateTimeField(blank=True, null=True)
    # Date of Exam
    date_of_result       = models.DateTimeField(blank=True, null=True)
    # Date report updated
    date_reported        = models.DateTimeField(blank=True, null=True)
    # Requesting Doctor NACS Code
    requesting_user_code = models.CharField(blank=True, null=True, max_length=255)
    requesting_user_name = models.CharField(blank=True, null=True, max_length=255)
    # Cerner Encounter ID
    cerner_visit_id      = models.CharField(blank=True, null=True, max_length=255)
    # Varchar(10) CRIS test code
    result_code          = models.CharField(blank=True, null=True, max_length=255)
    # Varchar(50) CRIS test description
    result_description   = models.CharField(blank=True, null=True, max_length=255)
    # P = Preliminary F = Final C = Corrected
    result_status        = models.CharField(blank=True, null=True, max_length=255)
    # CRIS Report seperated by <Seperator>
    obx_result           = models.TextField(blank=True, null=True)


    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        'SQL_Id'              : 'sql_id',
        'patient_number'      : 'patient_number',
        'patient_surname'     : 'patient_surname',
        'patient_forename'    : 'patient_forename',
        'result_id'           : 'result_id',
        'order_number'        : 'order_number',
        'order_effective_date': 'order_effective_date',
        'date_of_result'      : 'date_of_result',
        'date_reported'       : 'date_reported',
        'REQUESTING_USER_CODE': 'requesting_user_code',
        'REQUESTING_USER_NAME': 'requesting_user_name',
        'Cerner_VisitID'      : 'cerner_visit_id',
        'Result_Code'         : 'result_code',
        'Result_Description'  : 'result_description',
        'Result_Status'       : 'result_status',
        'OBX_Result'          : 'obx_result',
    }

    FIELDS_TO_SERIALIZE = [
        'result_id',
        'order_number',
        'order_effective_date',
        'date_of_result',
        'date_reported',
        'requesting_user_code',
        'requesting_user_name',
        'cerner_visitid',
        'result_code',
        'result_description',
        'result_status',
        'obx_result',
    ]

    def to_dict(self):
        return {k: getattr(self, k) for k in self.FIELDS_TO_SERIALIZE}
