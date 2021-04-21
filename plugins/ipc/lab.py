"""
Helpers for working with lab tests for the purposes of IPC
"""
from plugins.labtests import models as lab_test_models

from plugins.ipc import models



class IPCTest(object):

    TEST_NAME         = None # Name of the test (human readable & used to filter)
    TEST_CODE         = None # Winpath test code used for e.g. urls
    OBSERVATION_NAMES = []   # Names of the observation used to classify this test
    ALERT_CATEGORY    = None # The category of alert to use when creating an InfectionAlert for this test

    def __init__(self, test):
        self.test    = test
        self.patient = test.patient

    def __repr__(self):
        return "\n".join(
            [f"{self.test.lab_number} {self.test.test_code} {self.test.test_name} {self.test.datetime_ordered}"] +
            [f"{o.observation_name} {o.observation_value}" for o in self.get_observations()]
        )

    def get_observations(self):
        return self.test.observation_set.filter(
            observation_name__in=self.OBSERVATION_NAMES
        ).exclude(observation_value='.{}')

    def alert(self):
        """
        Is this test an alert result?
        """
        raise NotImplementedError()


class CarbapenemaseScreen(IPCTest):

    TEST_NAME         = 'CARBAPENEMASE SCREEN'
    TEST_CODE         = 'CARS'
    OBSERVATION_NAMES = ['Carbapenemase screen culture']
    ALERT_CATEGORY    = models.InfectionAlert.CPE

    def alert(self):
        """
        If the Screen grew something, return True otherwise return False
        """
        for observation in self.get_observations():
            if observation.observation_value.startswith('1'):
                return True
        return False


class CDiffPCR(IPCTest):

    TEST_NAME         = 'CDIFF PCR AND TOXIN'
    TEST_CODE         = 'DIFF'
    OBSERVATION_NAMES = ['C.diff PCR test', 'C.diff Toxin test']
    ALERT_CATEGORY    = models.InfectionAlert.CDIFF

    def alert(self):
        """
        If either observation is Positive, return True
        """
        for observation in self.get_observations():
            if observation.observation_value == 'POSITIVE':
                return True
        return False


class MRSAScreen(IPCTest):

    TEST_NAME         = 'MRSA SCREEN'
    TEST_CODE         = 'MRSA'
    OBSERVATION_NAMES = ['MRSA Culture result :']
    ALERT_CATEGORY    = models.InfectionAlert.MRSA

    def alert(self):
        """
        If the Culture grew something, return True otherwise return False
        """
        for observation in self.get_observations():
            if observation.observation_value.startswith('1'):
                return True
        return False


class TBCulture(IPCTest):
    TEST_NAME         = 'AFB : CULTURE'
    TEST_CODE         = 'AFB'
    OBSERVATION_NAMES = ['TB: Culture Result']
    ALERT_CATEGORY    = models.InfectionAlert.TB

    def alert(self):
        """
        TB Cultures are positive when they detail an organism
        """
        for observation in self.get_observations():
            if observation.observation_value.startswith('1'):
                return True
        return False


class TBPCR(IPCTest):
    TEST_NAME         = 'TB PCR TEST'
    TEST_CODE         = 'TBGX'
    OBSERVATION_NAMES = ['TB PCR']
    ALERT_CATEGORY    = models.InfectionAlert.TB

    def alert(self):
        """
        TB PCRs are positive when the word positive appears
        """
        for observation in self.get_observations():
            if 'positive' in observation.observation_value.lower():
                return True
        return False


IPC_TESTS = [CarbapenemaseScreen, CDiffPCR, MRSAScreen, TBCulture, TBPCR]

def get_test_instances(test, num=10, greedy=False):
    """
    Return instances of the IPCTest TEST, querying the LabTest data
    and casting appropriately.

    Defaults to 10, but can be altered with the kwarg NUM

    If the kwarg GREEDY is True, will return a generator that iterates
    through all tests of this type, all time.
    (Buyer beware, this can be time consuming.)
    """
    qs = lab_test_models.LabTest.objects.filter(
        lab_number__contains='L',
        test_name=test.TEST_NAME).order_by('-datetime_ordered')


    if greedy == False:
        return [test(instance) for instance in qs[:num]]

    def labtest_caster():
        for instance in qs:
            yield test(instance)

    return labtest_caster()


def get_test_class_by_code(code):
    """
    Given a test CODE return the IPCTest subclass related to that code
    """
    for test in IPC_TESTS:
        if test.TEST_CODE == code:
            return test
