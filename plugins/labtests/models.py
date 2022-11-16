import datetime
import re
from plugins.labtests import constants
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
    # the upstream 1-9 mapping that maps to the deparment
    # that performs this test
    department_int = models.IntegerField(null=True, blank=True)
    clinical_info = models.TextField(null=True, blank=True)
    datetime_ordered = models.DateTimeField(null=True, blank=True)
    site = models.CharField(max_length=256, blank=True, null=True)
    status = models.CharField(max_length=256, blank=True, null=True)
    test_code = models.CharField(max_length=256, blank=True, null=True)
    test_name = models.CharField(max_length=256, blank=True, null=True)
    lab_number = models.CharField(
        max_length=256, blank=True, null=True, db_index=True
    )
    accession_number = models.CharField(max_length=256, blank=True, null=True)
    encounter_consultant_name = models.CharField(max_length=256, blank=True, null=True)
    encounter_location_name = models.CharField(max_length=256, blank=True, null=True)
    encounter_location_code = models.CharField(max_length=256, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-datetime_ordered']

    def create_from_api_dict(self, patient, data):
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
        if data["datetime_ordered"]:
            self.datetime_ordered = serialization.deserialize_datetime(
                data["datetime_ordered"]
            )
        self.lab_number = data["external_identifier"]
        self.status = data["status"]
        self.test_code = data["test_code"]
        self.site = data["site"]
        self.test_name = data["test_name"]
        self.accession_number = data["accession_number"]
        self.department_int = data["department_int"]
        self.encounter_consultant_name = data["encounter_consultant_name"]
        self.encounter_location_name = data["encounter_location_name"]
        self.encounter_location_code = data["encounter_location_code"]
        self.save()
        observations = []
        for obs_dict in data["observations"]:
            observation =  Observation.translate_to_object(obs_dict)
            observation.test = self
            observations.append(observation)
        Observation.objects.bulk_create(observations)

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

    @property
    def cleaned_site(self):
        if not self.site:
            return ''
        values = []
        # Sometimes the description text includes a character
        # used as a separator, so rsplit
        for part in self.site.rsplit("&", 1):
            code_or_desc = [i for i in part.split('^') if i]
            if len(code_or_desc):
                values.append(code_or_desc[-1])
        return ' '.join([i.strip() for i in values if i.strip()])

    @property
    def site_code(self):
        """
        The site code that appears in capitals in the cleaned site.
        Note it can be "Sputa sample SPU" or "SPU Sputa sample"
        """
        cleaned_site = self.cleaned_site
        if not cleaned_site:
            return
        site_parts = cleaned_site.split(" ")
        for site_part in site_parts:
            if site_part.isupper():
                return site_part

    @property
    def department(self):
        return constants.WITHPATH_DEPATMENT_MAPPING.get(
            self.department_int
        )


class AbstractObserveration(models.Model):
    last_updated = models.DateTimeField(blank=True, null=True)
    observation_datetime = models.DateTimeField(blank=True, null=True)
    reported_datetime = models.DateTimeField(blank=True, null=True)
    observation_name = models.CharField(max_length=256, blank=True, null=True)
    observation_number = models.CharField(max_length=256, blank=True, null=True)
    observation_value = models.TextField(null=True, blank=True)
    reference_range = models.CharField(max_length=256, blank=True, null=True)
    units = models.CharField(max_length=256, blank=True, null=True)

    # as defined by us
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Observation(AbstractObserveration):
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)

    def to_float(self, some_val):
        regex = r'^[-+]?[0-9]+(\.[0-9]+)?$'
        if re.match(regex, some_val):
            return round(float(some_val), 3)

    @property
    def value_numeric(self):
        """
        if an observation is    , return it as a float
        some of the inputted values are messy, but essentially
        integers for example
        ' 12 ~ using new systyem as of Sep 2014
        If possible we clean this up and return a number
        otherwise return None
        """
        obs_result = self.observation_value.strip()
        obs_result = obs_result.split("~")[0].strip("<").strip(">").strip()
        return self.to_float(obs_result)

    @property
    def is_pending(self):
        return self.observation_value.lower() == "pending"

    @property
    def cleaned_reference_range(self):
        """
        reference ranges appear of the form
        1.5 - 4
        [      < 17     ]
        1-6
        -

        Clean these and handle them appropriately
        For the moment we will now pass < 17
        """
        reference_range = self.reference_range.replace("]", "").replace("[", "")
        regex = r"\s*([-+]?[0-9]+(\.[0-9]+)?)\s*-\s*([-+]?[0-9]+(\.[0-9]+)?)\s*?"
        matches = re.search(regex, reference_range)
        if not matches:
            return

        groups = matches.groups()

        min_val = groups[0]
        max_val = groups[2]

        if min_val is None or max_val is None:
            return

        return {
            "min": self.to_float(min_val),
            "max": self.to_float(max_val)
        }

    def is_outside_reference_range(self):
        """
        Returns True if the value is outside of the
        reference range.

        Returns False if the value is within the reference
        range.

        Returns None if we can't calculate the reference
        range or convert the value to a float.
        """
        rr = self.cleaned_reference_range
        value = self.value_numeric
        if rr is None or value is None:
            return
        if value < rr["min"]:
            return True
        if value > rr["max"]:
            return True
        return False

    @classmethod
    def translate_to_object(cls, observation_dict):
        """
        Returns a new unsaved instance of an Observation with the values
        from observation_dict (datetimes translated from strings into dates).
        """
        obs = cls()
        obs.last_updated = serialization.deserialize_datetime(
            observation_dict["last_updated"]
        )
        if observation_dict["observation_datetime"]:
            obs.observation_datetime = serialization.deserialize_datetime(
                observation_dict["observation_datetime"]
            )
        if observation_dict["reported_datetime"]:
            obs.reported_datetime = serialization.deserialize_datetime(
                observation_dict["reported_datetime"]
            )
        fields = [
            "observation_number",
            "observation_name",
            "observation_value",
            "reference_range",
            "units"
        ]
        for f in fields:
            setattr(obs, f, observation_dict.get(f))
        return obs


class ObservationHistory(AbstractObserveration):
    # the test_name of the tests that we will archive
    TEST_NAMES = [
        'AFB : CULTURE',
        'AFB : EARLY MORN. URINE',
        'AFB BLOOD CULTURE',
        'BLOOD CULTURE',
    ]
    test_name = models.CharField(max_length=256, blank=True, null=True)
    lab_number = models.CharField(max_length=256, blank=True, null=True)
    patient = models.ForeignKey(
        omodels.Patient,
        on_delete=models.CASCADE,
        related_name="observation_history"
    )
