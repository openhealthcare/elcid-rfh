import datetime
from unittest.mock import patch
from opal.core.test import OpalTestCase
from elcid import utils


class ModelMethodLoggingTestCase(OpalTestCase):

    def test_logging_method(self):
        class LoggingTest(object):
            id = 1

            @utils.model_method_logging
            def some_method(self):
                return "some_var"
        a = LoggingTest()
        with patch.object(utils.logger, "info") as info:
            with patch("elcid.utils.timezone.now") as now:
                first_call = datetime.datetime(2018, 2, 3, 10, 21)
                second_call = first_call + datetime.timedelta(minutes=1)
                now.side_effect = [first_call, second_call]
                result = a.some_method()
        first_call = info.call_args_list[0][0][0]
        second_call = info.call_args_list[1][0][0]
        self.assertEqual(
            first_call, "2018-02-03 10:21:00 starting LoggingTest.some_method \
(id 1)"
        )
        self.assertEqual(
            second_call,
            "2018-02-03 10:22:00 finishing LoggingTest.some_method (id 1) for \
2018-02-03 10:21:00"
        )
        self.assertEqual(
            result, "some_var"
        )


class GetPatientsFromMRNsTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def test_demographics_match(self):
        self.patient.demographics_set.update(
            hospital_number="123"
        )
        result = utils.find_patients_from_mrns(["123"])
        self.assertEqual(result["123"], self.patient)

    def test_demographics_zero_match(self):
        self.patient.demographics_set.update(
            hospital_number="123"
        )
        result = utils.find_patients_from_mrns(["0123"])
        self.assertEqual(result["0123"], self.patient)

    def test_ignore_empties(self):
        # we shouldn't have empty strings but if we
        # do we should not return them.
        self.patient.demographics_set.update(
            hospital_number=""
        )
        result = utils.find_patients_from_mrns([""])
        self.assertEqual(result, {})
        result = utils.find_patients_from_mrns(["000"])
        self.assertEqual(result, {})

    def test_merged_mrn_match(self):
        self.patient.demographics_set.update(
            hospital_number="234"
        )
        self.patient.mergedmrn_set.create(
            mrn="123"
        )
        result = utils.find_patients_from_mrns(["123"])
        self.assertEqual(result["123"], self.patient)

    def test_merged_mrn_zero_match(self):
        self.patient.demographics_set.update(
            hospital_number="234"
        )
        self.patient.mergedmrn_set.create(
            mrn="123"
        )
        result = utils.find_patients_from_mrns(["0123"])
        self.assertEqual(result["0123"], self.patient)

    def test_no_match(self):
        result = utils.find_patients_from_mrns(["123"])
        self.assertEqual(result, {})
