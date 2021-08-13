"""
Helpers for working with TB lab tests.
"""


from plugins.labtests.models import Observation
from django.db.models import Q


class TBObservation(object):
    TEST_NAMES = None
    OBSERVATION_NAME = None

    @classmethod
    def get_observations(cls):
        return Observation.objects.filter(
            test__test_name__in=cls.TEST_NAMES
        ).filter(
            observation_name=cls.OBSERVATION_NAME
        )

    @classmethod
    def get_positive_observations(cls):
        raise NotImplementedError("Please implement this")

    @classmethod
    def get_negative_observations(cls):
        raise NotImplementedError("Please implement this")

    @classmethod
    def get_resulted_observations(cls):
        return cls.get_positive_observations() | cls.get_negative_observations()


class AFBCulture(TBObservation):
    TEST_NAMES = [
        'AFB : CULTURE',
        'AFB : EARLY MORN. URINE',
        'AFB BLOOD CULTURE'
    ]
    OBSERVATION_NAME = 'TB: Culture Result'

    @classmethod
    def get_positive_observations(cls):
        return cls.get_observations().filter(
            observation_value__startswith="1"
        )

    @classmethod
    def get_negative_observations(cls):
        return cls.get_observations().filter(
            observation_value__startswith="No "
        )

    @classmethod
    def display_observation_value(cls, observation):
        return observation.observation_value.split("~")[0].lstrip("1)").strip()


class AFBSmear(TBObservation):
    TEST_NAMES = [
        'AFB : CULTURE',
        'AFB : EARLY MORN. URINE',
        'AFB BLOOD CULTURE'
    ]
    OBSERVATION_NAME = 'AFB Smear'

    @classmethod
    def get_positive_observations(cls):
        return cls.get_observations().filter(
            Q(observation_value__startswith="AAFB + Seen") |
            Q(observation_value__startswith="AAFB 2+ Seen") |
            Q(observation_value__startswith="AAFB 3+ Seen") |
            Q(observation_value__startswith="AAFB 4+ Seen")
        )

    @classmethod
    def get_negative_observations(cls):
        return cls.get_observations().filter(
            observation_value__startswith="AAFB not seen"
        )

    @classmethod
    def display_observation_value(cls, observation):
        return observation.observation_value.split("~")[0].strip()


class AFBRefLab(TBObservation):
    TEST_NAMES = [
        'AFB : CULTURE',
        'AFB : EARLY MORN. URINE',
        'AFB BLOOD CULTURE'
    ]
    OBSERVATION_NAME = 'TB Ref. Lab. Culture result'

    @classmethod
    def get_positive_observations(cls):
        return cls.get_observations().filter(
            observation_value__startswith="1"
        )

    @classmethod
    def get_negative_observations(cls):
        """
        Ref lab reports are always positive
        """
        return Observation.objects.none()

    @classmethod
    def display_observation_value(cls, observation):
        val = observation.observation_value.strip()
        to_remove = "\n".join([
            'Key: Susceptibility interpretation (Note: update to I)',
            'S = susceptible using standard dosing',
            'I= susceptible at increased dosing, high dose regimen must be used (please see your local antibiotic policy or Microguide for dosing guidance)',
            'R = resistant',
        ])
        return val.replace(to_remove, "").strip()


class TBPCR(TBObservation):
    TEST_NAMES = ['TB PCR TEST']
    OBSERVATION_NAME = 'TB PCR'

    @classmethod
    def get_negative_observations(cls):
        neg1 = "PCR to detect M.tuberculosis complex was~NEGATIVE"
        neg2 = "The PCR to detect M.tuberculosis complex was ~ NEGATIVE"
        return cls.get_observations().filter(
            Q(observation_value__contains=neg1) |
            Q(observation_value="TB PCR (GeneXpert) Negative") |
            Q(observation_value__contains=neg2),
        )

    @classmethod
    def get_positive_observations(cls):
        pos1 = "The PCR to detect M.tuberculosis complex was~POSITIVE"
        pos2 = "'The PCR to detect M.tuberculosis complex was ~ POSITIVE"
        return cls.get_observations().filter(
            Q(observation_value__contains=pos1) |
            Q(observation_value='TB PCR (GeneXpert) Positive') |
            Q(observation_value__contains=pos2)
        )

    @classmethod
    def display_observation_value(cls, observation):
        obs_value = observation.observation_value
        return obs_value.split("~")[0].strip()
