from plugins.labtests.models import LabTest, Observation
from elcid.utils import timing


class TBTest(object):
    TEST_NAME         = None # Name of the test (human readable & used to filter)
    TEST_CODE         = None # Winpath test codes
    OBSERVATION_NAMES = []   # Names of the observation(s) used to classify this test

    test = None  # Instance the test
    observations = None  # A list of the related observations with name OBSERVATION_NAMES
    date = None  # the date of the datetime ordered

    def __init__(self, test):
        self.test = test
        observations = self.test.observation_set.all()
        self.observations = [
            i for i in observations if i.observation_name in self.OBSERVATION_NAMES
        ]
        if test.datetime_ordered:
            self.date = test.datetime_ordered.date()

    def __repr__(self):
        return "\n".join(
            [f"{self.test.lab_number} {self.test.test_code} {self.test.test_name} {self.test.datetime_ordered}"] +
            [f"{o.observation_name} {o.observation_value}" for o in self.observations]
        )

    def positive_tb_obs(self):
        raise NotImplementedError()

    @classmethod
    def get_tb_tests(cls):
        return TB_TESTS

    @classmethod
    def get_tb_tests_for_patient(cls, patient):
        return cls.get_tests_for_patient(
            patient, cls.get_tb_tests()
        )

    @classmethod
    def get_ntm_tests_for_patient(cls, patient):
        return cls.get_tests_for_patient(
           patient, [TBCulture]
        )

    @classmethod
    def get_tests_for_patient(cls, patient, tests):
        test_names = set([
            i.TEST_NAME for i in tests
        ])
        return LabTest.objects.filter(
            patient=patient,
            test_name__in=test_names
        ).exclude(
            datetime_ordered=None
        ).prefetch_related(
            "observation_set"
        )

    @classmethod
    def cast_to_tb_test(cls, lab_test):
        tb_tests = cls.get_tb_tests()
        for tb_test in tb_tests:
            if lab_test.test_name == tb_test.TEST_NAME:
                return tb_test(lab_test)


class TBCulture(TBTest):
    TEST_NAME         = 'AFB : CULTURE'
    TEST_CODE         = 'AFB'
    OBSERVATION_NAMES = ['TB: Culture Result']
    PRIORITY          = 2

    def positive_tb_obs(self):
        for ob in self.observations:
            if ob.observation_value.startswith(
                "1) Mycobacterium tuberculosis"
            ):
                return ob

    def positive_ntm_obs(self):
        positive_values = [
            "1) Mycobacterium sp.",
            "1) Mycobacterium abscessus",
            "1) Mycobacterium kansasii",
        ]
        for ob in self.observations:
            for positive_start in positive_values:
                if ob.observation_value.startswith(positive_start):
                    return ob


class TBPCR(TBTest):
    TEST_NAME         = 'TB PCR TEST'
    TEST_CODE         = 'TBGX'
    OBSERVATION_NAMES = ['TB PCR']
    PRIORITY          = 1

    def positive_tb_obs(self):
        positive_values = [
            "The PCR to detect M.tuberculosis complex was~POSITIVE",
            "TB PCR (GeneXpert) Positive",
            "The PCR to detect M.tuberculosis complex was ~ POSITIVE",

        ]
        for ob in self.observations:
            for positive_start in positive_values:
                if ob.observation_value.startswith(positive_start):
                    return ob


class QuantiferonTBGold(TBTest):
    TEST_NAME         = 'QUANTIFERON TB GOLD IT'
    TEST_CODE         = 'QFT'
    OBSERVATION_NAMES = ['QFT TB interpretation']
    PRIORITY          = 3

    def positive_tb_obs(self):
        for ob in self.observations:
            if ob.observation_value.lower() == 'positive':
                return ob


TB_TESTS = sorted([TBCulture, TBPCR, QuantiferonTBGold], key=lambda x: x.PRIORITY)


def get_first_positive_tb(patient):
    qs = TBTest.get_tb_tests_for_patient(patient)
    qs = qs.order_by("datetime_ordered")
    first_positive = None
    for lab_test in qs:
        tb_test = TBTest.cast_to_tb_test(lab_test)
        if not tb_test.positive_tb_obs():
            continue
        if not first_positive:
            first_positive = tb_test
            continue
        if first_positive.date < tb_test.date:
            break
        if first_positive.PRIORITY < tb_test.PRIORITY:
            first_positive = tb_test
    return first_positive


def get_first_positive_ntm(patient):
    qs = TBCulture.get_ntm_tests_for_patient(patient)
    qs = qs.order_by(
        "datetime_ordered"
    )
    for lab_test in qs:
        cast_test = TBCulture(lab_test)
        if cast_test.positive_ntm_obs():
            return cast_test


@timing
def tb_tests_for_patient(patient):
    first_positive_tb = get_first_positive_tb(patient)
    first_positive_ntm = get_first_positive_ntm(patient)
    result = {}

    if first_positive_tb:
        obs_value = first_positive_tb.positive_tb_obs().observation_value
        result["first_tb_positive_date"] = first_positive_tb.date
        result["first_tb_positive_test_type"] = first_positive_tb.TEST_NAME
        result["first_tb_positive_obs_value"] = obs_value

    if first_positive_ntm:
        obs_value = first_positive_ntm.positive_ntm_obs().observation_value
        result["first_ntm_positive_date"] = first_positive_ntm.date
        result["first_ntm_positive_test_type"] = first_positive_ntm.TEST_NAME
        result["first_ntm_positive_obs_value"] = obs_value

    return result
