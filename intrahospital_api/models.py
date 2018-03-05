from django.db import models
from django.utils import timezone
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

    def start(self):
        self.started = timezone.now()
        self.state = self.RUNNING
        self.save()
        print "{} started at {}".format(
            self.verbose_name,
            self.started
        )

    @property
    def duration(self):
        if not self.stopped:
            raise ValueError(
                "%s has not finished yet" % self
            )
        return self.stopped - self.started

    def complete(self):
        self.stopped = timezone.now()
        self.state = self.SUCCESS
        self.save()
        print "{} successful at {}".format(
            self.verbose_name,
            self.stopped
        )
        print "{} {} succeeded in {}".format(
            self.verbose_name,
            self.id,
            self.duration.seconds
        )

    def failed(self):
        self.stopped = timezone.now()
        self.state = self.FAILURE
        self.save()
        print "{} failed at {}".format(
            self.verbose_name,
            self.stopped
        )
        print "{} {} failed in {}".format(
            self.verbose_name,
            self.id,
            self.duration.seconds
        )

    class Meta:
        abstract = True


class InitialPatientLoad(PatientLoad, PatientSubrecord):
    """ this model is the initial load of a patient
        future loads are done by the cron batch load
    """
    pass


class BatchPatientLoad(PatientLoad):
    class Meta:
        ordering = ('started',)
