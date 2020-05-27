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
    nhs_number      = models.CharField(max_length=255, blank=True, null=True)
    surname         = models.CharField(max_length=255, blank=True)
    first_name      = models.CharField(max_length=255, blank=True)
    middle_name     = models.CharField(max_length=255, blank=True, null=True)
    title           = ForeignKeyOrFreeText(omodels.Title)
    date_of_birth   = models.DateField(null=True, blank=True)
    sex             = ForeignKeyOrFreeText(omodels.Gender)
    ethnicity       = ForeignKeyOrFreeText(omodels.Ethnicity)
    death_indicator = models.BooleanField(
        default=False,
        help_text="This field will be True if the patient is deceased."
    )
    date_of_death   = models.DateField(
        null=True, blank=True, verbose_name="Date of Death"
    )


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
