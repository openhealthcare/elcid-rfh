import copy
import datetime
from django.db import models
from django.utils import timezone
from elcid.utils import model_method_logging
import opal.models as omodels
from opal.models import PatientSubrecord
from opal.core.fields import ForeignKeyOrFreeText


class ExternalDemographics(PatientSubrecord):
    _is_singleton = True
    _icon = "fa fa-handshake-o"

    hospital_number = models.CharField(max_length=255, blank=True)
    nhs_number = models.CharField(max_length=255, blank=True, null=True)
    surname = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    title = ForeignKeyOrFreeText(omodels.Title)
    date_of_birth = models.DateField(null=True, blank=True)
    sex = ForeignKeyOrFreeText(omodels.Gender)
    ethnicity = ForeignKeyOrFreeText(omodels.Ethnicity)


class PatientLoad(models.Model):
    RUNNING = "running"
    FAILURE = "failure"
    SUCCESS = "success"

    state = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    started = models.DateTimeField()
    stopped = models.DateTimeField(
        blank=True, null=True
    )
    count = models.IntegerField(
        blank=True, null=True
    )

    @property
    def verbose_name(self):
        return self.__class__._meta.verbose_name

    @model_method_logging
    def start(self):
        self.started = timezone.now()
        self.state = self.RUNNING
        self.save()

    @property
    def duration(self):
        if not self.stopped:
            raise ValueError(
                "%s has not finished yet" % self
            )
        return self.stopped - self.started

    @model_method_logging
    def complete(self):
        self.stopped = timezone.now()
        self.state = self.SUCCESS
        self.save()

    @model_method_logging
    def failed(self):
        self.stopped = timezone.now()
        self.state = self.FAILURE
        self.save()

    class Meta:
        abstract = True
        ordering = ('started',)


class InitialPatientLoad(PatientLoad, PatientSubrecord):
    """ This model is the initial load of a patient
        future loads are done by the cron batch load
    """

    def __str__(self):
        hospital_number = self.patient.demographics_set.first().hospital_number
        if self.stopped:
            return "{} {} {} {}".format(
                hospital_number,
                self.state,
                self.started,
                self.duration
            )
        else:
            return "{} {} {}".format(
                hospital_number,
                self.state,
                self.started
            )

    def update_from_dict(self, data, *args, **kwargs):
        """ For the purposes of the front end this model is read only.
        """
        pass


class BatchPatientLoad(PatientLoad):
    """ This is the batch load of all reconciled patients
        every 5 mins
    """

    def __str__(self):
        if self.stopped:
            return "{} {} {} {}".format(
                self.state,
                self.started,
                self.count,
                self.duration
            )
        else:
            return "{} {} {}".format(
                self.state,
                self.started,
                self.count
            )


class UpstreamLabTestRow(models.Model):
    opal_load_date = models.DateField(default=datetime.date.today())
    opal_created = models.DateTimeField(auto_now_add=True)
    opal_updated = models.DateTimeField(auto_now=True)
    Abnormal_Flag = models.TextField(blank=True, null=True)
    Accession_number = models.TextField(blank=True, null=True)
    CRS_ADDRESS_LINE1 = models.TextField(blank=True, null=True)
    CRS_ADDRESS_LINE2 = models.TextField(blank=True, null=True)
    CRS_ADDRESS_LINE3 = models.TextField(blank=True, null=True)
    CRS_ADDRESS_LINE4 = models.TextField(blank=True, null=True)
    CRS_DOB = models.DateTimeField(blank=True, null=True)
    CRS_Date_of_Death = models.DateTimeField(blank=True, null=True)
    CRS_Deceased_Flag = models.TextField(blank=True, null=True)
    CRS_EMAIL = models.TextField(blank=True, null=True)
    CRS_Ethnic_Group = models.TextField(blank=True, null=True)
    CRS_Forename1 = models.TextField(blank=True, null=True)
    CRS_Forename2 = models.TextField(blank=True, null=True)
    CRS_GP_NATIONAL_CODE = models.TextField(blank=True, null=True)
    CRS_GP_PRACTICE_CODE = models.TextField(blank=True, null=True)
    CRS_HOME_TELEPHONE = models.TextField(blank=True, null=True)
    CRS_MAIN_LANGUAGE = models.TextField(blank=True, null=True)
    CRS_MARITAL_STATUS = models.TextField(blank=True, null=True)
    CRS_MOBILE_TELEPHONE = models.TextField(blank=True, null=True)
    CRS_NATIONALITY = models.TextField(blank=True, null=True)
    CRS_NHS_Number = models.TextField(blank=True, null=True)
    CRS_NOK_ADDRESS1 = models.TextField(blank=True, null=True)
    CRS_NOK_ADDRESS2 = models.TextField(blank=True, null=True)
    CRS_NOK_ADDRESS3 = models.TextField(blank=True, null=True)
    CRS_NOK_ADDRESS4 = models.TextField(blank=True, null=True)
    CRS_NOK_FORENAME1 = models.TextField(blank=True, null=True)
    CRS_NOK_FORENAME2 = models.TextField(blank=True, null=True)
    CRS_NOK_HOME_TELEPHONE = models.TextField(blank=True, null=True)
    CRS_NOK_MOBILE_TELEPHONE = models.TextField(blank=True, null=True)
    CRS_NOK_POST_CODE = models.TextField(blank=True, null=True)
    CRS_NOK_RELATIONSHIP = models.TextField(blank=True, null=True)
    CRS_NOK_SURNAME = models.TextField(blank=True, null=True)
    CRS_NOK_TYPE = models.TextField(blank=True, null=True)
    CRS_NOK_WORK_TELEPHONE = models.TextField(blank=True, null=True)
    CRS_Postcode = models.TextField(blank=True, null=True)
    CRS_Religion = models.TextField(blank=True, null=True)
    CRS_SEX = models.TextField(blank=True, null=True)
    CRS_Surname = models.TextField(blank=True, null=True)
    CRS_Title = models.TextField(blank=True, null=True)
    CRS_WORK_TELEPHONE = models.TextField(blank=True, null=True)
    DOB = models.DateTimeField(blank=True, null=True)
    Date_Last_Obs_Normal = models.DateTimeField(blank=True, null=True)
    Date_of_the_Observation = models.DateTimeField(blank=True, null=True)
    Department = models.TextField(blank=True, null=True)
    Encounter_Consultant_Code = models.TextField(blank=True, null=True)
    Encounter_Consultant_Name = models.TextField(blank=True, null=True)
    Encounter_Consultant_Type = models.TextField(blank=True, null=True)
    Encounter_Location_Code = models.TextField(blank=True, null=True)
    Encounter_Location_Name = models.TextField(blank=True, null=True)
    Encounter_Location_Type = models.TextField(blank=True, null=True)
    Event_Date = models.DateTimeField(blank=True, null=True)
    Firstname = models.TextField(blank=True, null=True)
    MSH_Control_ID = models.TextField(blank=True, null=True)
    obr_id = models.IntegerField(blank=True, null=True)
    OBR_Priority = models.TextField(blank=True, null=True, verbose_name="OBR-5_Priority")
    OBR_Sequence_ID = models.TextField(blank=True, null=True)
    OBR_Status = models.TextField(blank=True, null=True)
    OBR_exam_code_ID = models.TextField(blank=True, null=True)
    OBR_exam_code_Text = models.TextField(blank=True, null=True)
    OBX_Sequence_ID = models.TextField(blank=True, null=True)
    OBX_Status = models.TextField(blank=True, null=True)
    OBX_exam_code_ID = models.TextField(blank=True, null=True)
    OBX_exam_code_Text = models.TextField(blank=True, null=True)
    OBX_id = models.IntegerField(blank=True, null=True)
    ORC_Datetime_of_Transaction = models.DateTimeField(
        blank=True, null=True, verbose_name="ORC-9_Datetime_of_Transaction"
    )
    Observation_date = models.DateTimeField(blank=True, null=True)
    Order_Number = models.CharField(max_length=256, blank=True, null=True)
    Patient_Class = models.TextField(blank=True, null=True)
    Patient_ID_External = models.TextField(blank=True, null=True)
    Patient_Number = models.TextField(blank=True, null=True)
    PV1_7_C_NUMBER = models.TextField(blank=True, null=True)
    PV1_7_CONSULTANT_NAME = models.TextField(blank=True, null=True)
    PV1_3_5 = models.TextField(blank=True, null=True)
    PV1_3_9 = models.TextField(blank=True, null=True)
    Relevant_Clinical_Info = models.TextField(blank=True, null=True)
    Reported_date = models.DateTimeField(blank=True, null=True)
    Request_Date = models.DateTimeField(blank=True, null=True)
    Requesting_Clinician = models.TextField(blank=True, null=True)
    Result_ID = models.TextField(blank=True, null=True)
    Result_Range = models.TextField(blank=True, null=True)
    Result_Units = models.TextField(blank=True, null=True)
    Result_Value = models.TextField(blank=True, null=True)

    # either RF or BCF (royal free or Barnet/Chase Farm)
    result_source = models.TextField(blank=True, null=True)
    SEX = models.TextField(blank=True, null=True)
    Specimen_Site = models.CharField(max_length=256, blank=True, null=True)
    Surname = models.TextField(blank=True, null=True)
    Visit_Number = models.TextField(blank=True, null=True)
    crs_patient_masterfile_id = models.TextField(blank=True, null=True)
    date_inserted = models.DateTimeField(blank=True, null=True)

    # is id in the upstream
    upstream_id = models.IntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    visible = models.TextField(blank=True, null=True)

    @classmethod
    def create(cls, lab_test_row):
        row = copy.copy(lab_test_row)
        row["upstream_id"] = row.pop("id")
        row["ORC_Datetime_of_Transaction"] = row.pop(
            "ORC-9_Datetime_of_Transaction"
        )
        row["OBR_Priority"] = row.pop("OBR-5_Priority")
        for k, v in row.items():
            if isinstance(row, datetime.datetime):
                row[k] = timezone.make_aware(row[k])
        return cls.objects.create(**row)
