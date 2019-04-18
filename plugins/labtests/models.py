import datetime
from django.utils.dateformat import format as dt_format
from django.db import models
from django.conf import settings
from django.utils import timezone
from opal.core import serialization
from opal import models as omodels


def format_dt(some_dt):
    if some_dt:
        return dt_format(some_dt, settings.DATETIME_FORMAT)


"""
Models for labtests
"""
class LabTest(models.Model):
    patient = models.ForeignKey(
        omodels.Patient,
        on_delete=models.CASCADE,
        related_name="lab_tests"
    )
    clinical_info = models.TextField(blank=True)
    datetime_ordered = models.DateTimeField(null=True, blank=True)
    site = models.CharField(max_length=256, blank=True, null=True)
    status = models.CharField(max_length=256, blank=True, null=True)
    test_code = models.CharField(max_length=256, blank=True, null=True)
    test_name = models.CharField(max_length=256, blank=True, null=True)
    lab_number = models.CharField(max_length=256, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-datetime_ordered']

    @classmethod
    def create_from_old_test(cls, old_lab_test):
        new_lab_test = cls()
        new_lab_test.patient = old_lab_test.patient
        extras = old_lab_test.extras
        fields = [
            "clinical_info",
            "site",
            "status",
            "test_code",
            "test_name",
            "lab_number",
        ]
        for f in fields:
            setattr(s, f, extras.get(f, None))
        new_lab_test.datetime_ordered = old_lab_test.datetime_ordered
        new_lab_test.lab_number = old_lab_test.external_identifier
        new_lab_test.save()
        for ob in extras["observations"]:
            obs = old_lab_test.observation_set.create()
            obs.create(ob)
        return new_lab_test

    def update_from_api_dict(self, patient, data):
        """
            This is the updateFromDict of the the UpstreamLabTest

            We expect something like the following

            {
                clinical_info:  u'testing',
                datetime_ordered: "18/07/2015, 04:15",
                external_identifier: "11111",
                site: u'^&                              ^',
                status: "Sucess",
                test_code: "AN12"
                test_name: "Anti-CV2 (CRMP-5) antibodies",
                observations: [{
                    "last_updated": "18/07/2015, 04:15",
                    "observation_datetime": "18/07/2015, 04:15"
                    "observation_name": "Aerobic bottle culture",
                    "observation_number": "12312",
                    "reference_range": "3.5 - 11",
                    "units": "g"
                }]
            }
        """
        self.patient = patient
        self.clinical_info = data["clinical_info"]
        self.datetime_ordered = serialization.deserialize_datetime(
            data["datetime_ordered"]
        )
        self.lab_number = data["external_identifier"]
        self.status = data["status"]
        self.test_code = data["test_code"]
        self.site = data["site"]
        self.test_name = data["test_name"]
        self.save()
        for obs_dict in data["observations"]:
            obs = self.observation_set.filter(
                observation_number=obs_dict["observation_number"]
            )
            if obs.exists():
                obs.delete()

            obs = self.observation_set.create()
            obs.create(obs_dict)


    @property
    def extras(self):
        fields = [
            "clinical_info",
            "site",
            "status",
            "test_code",
            "test_name",
            "lab_number",
        ]
        result = {}
        for field in fields:
            result[field] = getattr(self, field)

        result["observations"] = [
            i.to_dict() for i in self.observation_set.all()
        ]
        return result

    @classmethod
    def get_relevant_tests(self, patient):
        relevent_tests = [
            "C REACTIVE PROTEIN",
            "FULL BLOOD COUNT",
            "UREA AND ELECTROLYTES",
            "LIVER FUNCTION",
            "LIVER PROFILE",
            "GENTAMICIN LEVEL",
            "CLOTTING SCREEN"
        ]
        three_weeks_ago = timezone.now() - datetime.timedelta(3*7)
        qs = LabTest.objects.filter(
            patient=patient,
            datetime_ordered__gt=three_weeks_ago
        ).order_by("datetime_ordered")
        return [i for i in qs if i.extras.get("test_name") in relevent_tests]

    def dict_for_view(self, user):
        result = self.extras
        result["datetime_ordered"] = self.datetime_ordered
        result["extras"] = self.extras
        return result


class Observation(models.Model):
    # as created in the upstream db
    last_updated = models.DateTimeField(blank=True, null=True)
    observation_datetime = models.DateTimeField(blank=True, null=True)
    observation_name = models.CharField(max_length=256, blank=True, null=True)
    observation_number = models.CharField(max_length=256, blank=True, null=True)
    observation_value = models.TextField(blank=True)
    reference_range = models.CharField(max_length=256, blank=True, null=True)
    units = models.CharField(max_length=256, blank=True, null=True)
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)

    # as defined by us
    created_at = models.DateTimeField(auto_now_add=True)

    def create(self, observation_dict):
        self.last_updated = serialization.deserialize_datetime(
            observation_dict["last_updated"]
        )
        self.observation_datetime = serialization.deserialize_datetime(
            observation_dict["observation_datetime"]
        )
        fields = [
            "observation_number",
            "observation_name",
            "observation_value",
            "reference_range",
            "units"
        ]
        for f in fields:
            setattr(self, f, observation_dict.get(f))
        self.save()
        return self

    def to_dict(self):
        as_dict = {}
        as_dict["last_updated"] = format_dt(self.last_updated)
        as_dict["observation_datetime"] = format_dt(self.observation_datetime)
        fields = [
            "observation_number",
            "observation_name",
            "observation_value",
            "reference_range",
            "units"
        ]
        for field in fields:
            as_dict[field] = getattr(self, field)
        return as_dict

