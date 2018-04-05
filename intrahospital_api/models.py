from django.db import models
from django.utils import timezone
import opal.models as omodels
from opal.models import PatientSubrecord
from opal.core.fields import ForeignKeyOrFreeText
from elcid.utils import datetime_to_str


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

    @property
    def started_str(self):
        if self.started:
            return datetime_to_str(self.started)

    @property
    def stopped_str(self):
        if self.stopped:
            return datetime_to_str(self.stopped)

    def complete(self):
        self.stopped = timezone.now()
        self.state = self.SUCCESS
        self.save()

    def failed(self):
        self.stopped = timezone.now()
        self.state = self.FAILURE
        self.save()

    class Meta:
        abstract = True
        ordering = ('-started',)


class InitialPatientLoad(PatientLoad, PatientSubrecord):
    """ this model is the initial load of a patient
        future loads are done by the cron batch load
    """
    def __str__(self):
        return "{} {} {} {}".format(
            self.verbose_name,
            self.patient_id,
            self.started_str,
            self.stopped_str,
            self.state
        )


class BatchPatientLoad(PatientLoad):
    """ This is the batch load of all reconciled patients
        every 5 mins
    """
    def __str__(self):
        return "{} {} {} {}".format(
            self.verbose_name,
            self.started_str,
            self.stopped_str,
            self.count,
            self.state
        )
