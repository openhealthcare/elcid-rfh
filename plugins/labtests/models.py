from django.db import models
from opal.core import serialization
from opal import models as omodels
from opal.core.exceptions import APIError
from lab import models as lab_models


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
    result_id = models.CharField(max_length=256, blank=True, null=True)

    @classmethod
    def create(cls, lt):
        s = cls()
        s.patient = lt.patient
        extras = lt.extras
        fields = [
            "clinical_info",
            "site",
            "status",
            "test_code",
            "test_name",
        ]
        for f in fields:
            setattr(s, f, extras.get(f, None))
        s.datetime_ordered = lt.datetime_ordered
        s.result_id = lt.external_identifier
        s.save()
        for i in extras["observations"]:
            Obs.create(s, i)
        return s

    @property
    def extras(self):
        fields = [
            "clinical_info",
            "site",
            "status",
            "test_code",
            "test_name",
        ]
        result = {}
        for field in fields:
            result[field] = getattr(self, field)

        result["observations"] = {
            i.to_dict() for i in self.observation_set.all()
        }
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


class Observation(models.Model):
    last_updated = models.DateTimeField(blank=True, null=True)
    observation_datetime = models.DateTimeField(blank=True, null=True)
    observation_name = models.CharField(max_length=256, blank=True, null=True)
    observation_number = models.CharField(max_length=256, blank=True, null=True)
    observation_value = models.TextField(blank=True)
    reference_range = models.CharField(max_length=256, blank=True, null=True)
    units = models.CharField(max_length=256, blank=True, null=True)
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)

    @classmethod
    def create(cls, test, observation_dict):
        o = cls()
        o.test = test
        o.last_updated = serialization.deserialize_datetime(
            observation_dict["last_updated"]
        )
        o.observation_datetime = serialization.deserialize_datetime(
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
            setattr(o, f, observation_dict.get(f))
        o.save()
        return o

    def to_dict(self):
        fields = self._meta.get_fields()
        fields = [i for i in fields if i not in {"id", "test"}]
        return {i: getattr(self, i) for i in fields}


def create_from_old_tests(patient):
    for ut in patient.labtest_set.filter(
        lab_test_type__istartswith="up"
    ):
        LabTest.create(ut)
