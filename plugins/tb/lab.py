"""
Helpers for working with TB lab tests.
"""


from plugins.labtests.models import Observation
from django.db.models import Q


class TBTest(object):
    TEST_NAME = None
    TEST_CODE = None
    OBSERVATION_NAME = None

    @classmethod
    def get_observations(cls):
        return Observation.objects.filter(
            test__test_name=cls.TEST_NAME
        ).filter(
            test__test_code=cls.TEST_CODE
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

    @classmethod
    def get_last_resulted_observation(cls, patient):
        last_negative = cls.get_negative_observations().filter(
            test__patient=patient
        ).order_by(
            "-test__datetime_ordered"
        ).first()
        last_positive = cls.get_positive_observations().filter(
            test__patient=patient
        ).order_by(
            "-test__datetime_ordered"
        ).first()
        if last_negative and last_positive:
            last_negative_date = last_negative.test.datetime_ordered.date()
            last_positive_date = last_positive.test.datetime_ordered.date()
            if last_negative_date > last_positive_date:
                return last_negative
            return last_positive
        return last_positive or last_negative

    @classmethod
    def get_first_resulted_observation(cls, patient):
        first_negative = cls.get_negative_observations().filter(
            test__patient=patient
        ).order_by(
            "-test__datetime_ordered"
        ).first()
        first_positive = cls.get_positive_observations().filter(
            test__patient=patient
        ).order_by(
            "-test__datetime_ordered"
        ).first()
        if first_negative and first_positive:
            first_negative_date = first_negative.test.datetime_ordered.date()
            first_positive_date = first_positive.test.datetime_ordered.date()
            if first_negative_date > first_positive_date:
                return first_negative
            return first_positive


class AFBCulture(TBTest):
    TEST_NAME = 'AFB : CULTURE'
    TEST_CODE = 'AFB'
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


class AFBSmear(TBTest):
    TEST_NAME = 'AFB : CULTURE'
    TEST_CODE = 'AFB'
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


class TBPCR(TBTest):
    TEST_NAME = 'TB PCR TEST'
    TEST_CODE = "TBGX"
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
            Q(observation_name='TB PCR (GeneXpert) Positive') |
            Q(observation_value__contains=pos2)
        )
