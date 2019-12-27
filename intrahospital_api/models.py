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
    Abnormal_Flag = models.CharField(max_length=256, default="")
    Accession_number = models.CharField(max_length=256, default="")
    CRS_ADDRESS_LINE1 = models.CharField(max_length=256, default="")
    CRS_ADDRESS_LINE2 = models.CharField(max_length=256, default="")
    CRS_ADDRESS_LINE3 = models.CharField(max_length=256, default="")
    CRS_ADDRESS_LINE4 = models.CharField(max_length=256, default="")
    CRS_DOB = models.DateTimeField(blank=True, null=True)
    CRS_Date_of_Death = models.DateTimeField(blank=True, null=True)
    CRS_Deceased_Flag = models.CharField(max_length=256, default="")
    CRS_EMAIL = models.CharField(max_length=256, default="")
    CRS_Ethnic_Group = models.CharField(max_length=256, default="")
    CRS_Forename1 = models.CharField(max_length=256, default="")
    CRS_Forename2 = models.CharField(max_length=256, default="")
    CRS_GP_NATIONAL_CODE = models.CharField(max_length=256, default="")
    CRS_GP_PRACTICE_CODE = models.CharField(max_length=256, default="")
    CRS_HOME_TELEPHONE = models.CharField(max_length=256, default="")
    CRS_MAIN_LANGUAGE = models.CharField(max_length=256, default="")
    CRS_MARITAL_STATUS = models.CharField(max_length=256, default="")
    CRS_MOBILE_TELEPHONE = models.CharField(max_length=256, default="")
    CRS_NATIONALITY = models.CharField(max_length=256, default="")
    CRS_NHS_Number = models.CharField(max_length=256, default="")
    CRS_NOK_ADDRESS1 = models.CharField(max_length=256, default="")
    CRS_NOK_ADDRESS2 = models.CharField(max_length=256, default="")
    CRS_NOK_ADDRESS3 = models.CharField(max_length=256, default="")
    CRS_NOK_ADDRESS4 = models.CharField(max_length=256, default="")
    CRS_NOK_FORENAME1 = models.CharField(max_length=256, default="")
    CRS_NOK_FORENAME2 = models.CharField(max_length=256, default="")
    CRS_NOK_HOME_TELEPHONE = models.CharField(max_length=256, default="")
    CRS_NOK_MOBILE_TELEPHONE = models.CharField(max_length=256, default="")
    CRS_NOK_POST_CODE = models.CharField(max_length=256, default="")
    CRS_NOK_RELATIONSHIP = models.CharField(max_length=256, default="")
    CRS_NOK_SURNAME = models.CharField(max_length=256, default="")
    CRS_NOK_TYPE = models.CharField(max_length=256, default="")
    CRS_NOK_WORK_TELEPHONE = models.CharField(max_length=256, default="")
    CRS_Postcode = models.CharField(max_length=256, default="")
    CRS_Religion = models.CharField(max_length=256, default="")
    CRS_SEX = models.CharField(max_length=256, default="")
    CRS_Surname = models.CharField(max_length=256, default="")
    CRS_Title = models.CharField(max_length=256, default="")
    CRS_WORK_TELEPHONE = models.CharField(max_length=256, default="")
    DOB = models.DateTimeField(blank=True, null=True)
    Date_Last_Obs_Normal = models.DateTimeField(blank=True, null=True)
    Date_of_the_Observation = models.DateTimeField(blank=True, null=True)
    Department = models.CharField(max_length=256, default="")
    Encounter_Consultant_Code = models.CharField(max_length=256, default="")
    Encounter_Consultant_Name = models.CharField(max_length=256, default="")
    Encounter_Consultant_Type = models.CharField(max_length=256, default="")
    Encounter_Location_Code = models.CharField(max_length=256, default="")
    Encounter_Location_Name = models.CharField(max_length=256, default="")
    Encounter_Location_Type = models.CharField(max_length=256, default="")
    Event_Date = models.DateTimeField(blank=True, null=True)
    Firstname = models.CharField(max_length=256, default="")
    MSH_Control_ID = models.CharField(max_length=256, default="")
    OBR_Priority = models.CharField(
        max_length=256, default="", verbose_name="OBR-5_Priority"
    )
    OBR_Sequence_ID = models.CharField(max_length=256, default="")
    OBR_Status = models.CharField(max_length=256, default="")
    OBR_exam_code_ID = models.CharField(max_length=256, default="")
    OBR_exam_code_Text = models.CharField(max_length=256, default="")
    OBX_Sequence_ID = models.CharField(max_length=256, default="")
    OBX_Status = models.CharField(max_length=256, default="")
    OBX_exam_code_ID = models.CharField(max_length=256, default="")
    OBX_exam_code_Text = models.CharField(max_length=256, default="")
    OBX_id = models.IntegerField(blank=True, null=True)
    ORC_Datetime_of_Transaction = models.DateTimeField(
        blank=True, null=True, verbose_name="ORC-9_Datetime_of_Transaction"
    )
    Observation_date = models.DateTimeField(blank=True, null=True)
    Order_Number = models.CharField(max_length=256, default="")
    Patient_Class = models.CharField(max_length=256, default="")
    Patient_ID_External = models.CharField(max_length=256, default="")
    Patient_Number = models.CharField(max_length=256, default="")
    Relevant_Clinical_Info = models.CharField(max_length=256, default="")
    Reported_date = models.DateTimeField(blank=True, null=True)
    Request_Date = models.DateTimeField(blank=True, null=True)
    Requesting_Clinician = models.CharField(max_length=256, default="")
    Result_ID = models.CharField(max_length=256, default="")
    Result_Range = models.CharField(max_length=256, default="")
    Result_Units = models.CharField(max_length=256, default="")
    Result_Value = models.CharField(max_length=256, default="")
    SEX = models.CharField(max_length=256, default="")
    Specimen_Site = models.CharField(max_length=256, default="")
    Surname = models.CharField(max_length=256, default="")
    Visit_Number = models.CharField(max_length=256, default="")
    crs_patient_masterfile_id = models.CharField(
        max_length=256, blank=True, null=True
    )
    date_inserted = models.DateTimeField(blank=True, null=True)

    # is id in the upstream
    upstream_id = models.IntegerField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    visible = models.CharField(max_length=256, default="")

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
