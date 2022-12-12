import datetime
from unittest.mock import patch
from opal.core.test import OpalTestCase
from elcid import utils
from elcid import episode_categories
from plugins.tb import episode_categories as tb_episode_categories


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


class GetOrCreatePatientTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def test_get_existing_patient(self):
        self.patient.demographics_set.update(hospital_number="123")
        self.patient.episode_set.update(
            category_name=episode_categories.InfectionService.display_name
        )
        patient, created = utils.get_or_create_patient(
            '123', episode_categories.InfectionService
        )
        self.assertEqual(self.patient, patient)
        episode = self.patient.episode_set.get()
        self.assertEqual(
            episode.category_name,
            episode_categories.InfectionService.display_name
        )
        self.assertFalse(created)

    def test_create_new_episode_on_existing_patient(self):
        self.patient.demographics_set.update(hospital_number="123")
        patient, created = utils.get_or_create_patient(
            '123', tb_episode_categories.TbEpisode
        )
        self.assertEqual(self.patient, patient)
        self.assertTrue(self.patient.episode_set.filter(
            category_name=tb_episode_categories.TbEpisode.display_name
        ).exists())
        self.assertFalse(created)

    @patch('intrahospital_api.loader.create_rfh_patient_from_hospital_number')
    def test_get_merged_patient(self, create_rfh_patient_from_hospital_number):
        self.patient.demographics_set.update(hospital_number="234")
        self.patient.mergedmrn_set.create(mrn="123")
        patient, created = utils.get_or_create_patient(
            '123', episode_categories.InfectionService
        )
        self.assertEqual(
            patient.id, self.patient.id
        )
        self.assertFalse(create_rfh_patient_from_hospital_number.called)
        self.assertFalse(created)

    @patch('intrahospital_api.loader.create_rfh_patient_from_hospital_number')
    def test_create_new_patient(self, create_rfh_patient_from_hospital_number):
        create_rfh_patient_from_hospital_number.return_value = self.patient
        patient, created = utils.get_or_create_patient(
            '123', episode_categories.InfectionService
        )
        create_rfh_patient_from_hospital_number.assert_called_once_with(
            '123',
            episode_categories.InfectionService,
            run_async=None
        )
        self.assertEqual(self.patient, patient)
        self.assertTrue(created)


class FindPatientsFromMRNsTestCase(OpalTestCase):
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
