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

class GetPatientTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def test_get_existing_patient(self):
        self.patient.demographics_set.update(hospital_number="123")
        patient = utils.get_patient('123')
        self.assertEqual(self.patient, patient)

    def test_get_existing_merged_patient(self):
        self.patient.demographics_set.update(hospital_number="123")
        self.patient.mergedmrn_set.create(
            mrn="234"
        )
        patient = utils.get_patient('234')
        self.assertEqual(self.patient, patient)

class GetOrCreatePatientTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def test_get_existing_patient(self):
        self.patient.demographics_set.update(hospital_number="123")
        patient, created = utils.get_or_create_patient('123')
        self.assertEqual(self.patient, patient)
        self.assertFalse(created)

    @patch('intrahospital_api.update_demographics.upstream_merged_mrn')
    @patch('intrahospital_api.loader.create_rfh_patient_from_hospital_number')
    def test_create_new_patient(self, create_rfh_patient, upstream_merged_mrn):
        create_rfh_patient.return_value = self.patient
        upstream_merged_mrn.return_value = None
        patient, created = utils.get_or_create_patient('123')
        create_rfh_patient.assert_called_once_with('123', run_async=None)
        self.assertEqual(self.patient, patient)
        self.assertTrue(created)

    @patch('intrahospital_api.update_demographics.upstream_merged_mrn')
    @patch('intrahospital_api.loader.create_rfh_patient_from_hospital_number')
    def test_create_merged_patient(self, create_rfh_patient, upstream_merged_mrn):
        create_rfh_patient.return_value = self.patient
        upstream_merged_mrn.return_value = "234"
        patient, created = utils.get_or_create_patient('123')
        create_rfh_patient.assert_called_once_with('234', run_async=None)
        self.assertEqual(self.patient, patient)
        self.assertTrue(created)
