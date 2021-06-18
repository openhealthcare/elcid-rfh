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


class Sputum(TBTest):
    TEST_NAME = "SPUTUM CULTURE"
    TEST_CODE = "SPC"
    OBSERVATION_NAME = "Culture Result"

    @classmethod
    def get_positive_observations(cls):
        return cls.get_observations().filter(
            observation_value__startswith="1)"
        )

    @classmethod
    def get_negative_observations(cls):
        return cls.get_observations().filter(
            Q(observation_value__istartswith="Normal Respiratory tract flora"),
            Q(observation_value__istartswith="No growth after"),
            Q(observation_value__istartswith="No Bacterial growth"),
        )

    @classmethod
    def display_observation_value(cls, observation):
        return observation.observation_value.split("~")[0].lstrip("1)").strip()
