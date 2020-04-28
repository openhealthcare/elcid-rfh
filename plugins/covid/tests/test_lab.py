"""
Unittests for the plugins.covid.lab module
"""
from django.utils import timezone
from opal.core.test import OpalTestCase

from plugins.covid import lab

class GetResultTestCase(OpalTestCase):

    def test_get_result(self):
        p, e = self.new_patient_and_episode_please()
        test = p.lab_tests.create(
            test_name="2019 NOVEL CORONAVIRUS",
            datetime_ordered=timezone.now(),
            patient=p
        )
        observation = test.observation_set.create(
            observation_name='2019 nCoV',
            observation_value='POSITIVE'
        )
        self.assertEqual('POSITIVE', lab.get_result(test))


class ResultedTestCase(OpalTestCase):

    def test_resulted(self):
        p, e = self.new_patient_and_episode_please()
        test = p.lab_tests.create(
            test_name="2019 NOVEL CORONAVIRUS",
            datetime_ordered=timezone.now(),
            patient=p
        )
        observation = test.observation_set.create(
            observation_name='2019 nCoV',
            observation_value='POSITIVE'
        )
        self.assertTrue(lab.resulted(test))


    def test_not_resulted(self):
        p, e = self.new_patient_and_episode_please()
        test = p.lab_tests.create(
            test_name="2019 NOVEL CORONAVIRUS",
            datetime_ordered=timezone.now(),
            patient=p
        )
        observation = test.observation_set.create(
            observation_name='2019 nCoV',
            observation_value='Pending'
        )
        self.assertFalse(lab.resulted(test))


class PositiveTestCase(OpalTestCase):

    def test_positive(self):
        p, e = self.new_patient_and_episode_please()
        test = p.lab_tests.create(
            test_name="2019 NOVEL CORONAVIRUS",
            datetime_ordered=timezone.now(),
            patient=p
        )
        observation = test.observation_set.create(
            observation_name='2019 nCoV',
            observation_value='POSITIVE'
        )
        self.assertTrue(lab.positive(test))


    def test_not_positive(self):
        p, e = self.new_patient_and_episode_please()
        test = p.lab_tests.create(
            test_name="2019 NOVEL CORONAVIRUS",
            datetime_ordered=timezone.now(),
            patient=p
        )
        observation = test.observation_set.create(
            observation_name='2019 nCoV',
            observation_value='Pending'
        )
        self.assertFalse(lab.positive(test))
