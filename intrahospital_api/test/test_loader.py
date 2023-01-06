from unittest import mock
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from opal.core.test import OpalTestCase
from elcid import episode_categories
from intrahospital_api import models as imodels
from intrahospital_api import loader
from plugins.labtests import models as lab_test_models


@override_settings(API_USER="ohc")
class ApiTestCase(OpalTestCase):
    def setUp(self):
        super(ApiTestCase, self).setUp()
        User.objects.create(username="ohc", password="fake_password")

@mock.patch(
    "intrahospital_api.loader.api.results_for_hospital_number",
    __name__="results_for_hospital_number"
)
@mock.patch(
    "intrahospital_api.loader.update_demographics.update_patient_information",
    __name__="update_patient_information"
)
@mock.patch(
    "intrahospital_api.loader.load_imaging",
    __name__="load_imaging"
)
@mock.patch(
    "intrahospital_api.loader.load_encounters",
    __name__="load_encounters"
)
@mock.patch(
    "intrahospital_api.loader.load_transfer_history_for_patient",
    __name__="load_transfer_history_for_patient"
)
@mock.patch(
    "intrahospital_api.loader.load_appointments",
    __name__="load_appointments"
)
@mock.patch(
    "intrahospital_api.loader.logger",
)
class _LoadPatientTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.initial_patient_load = self.patient.initialpatientload_set.create(
            started=timezone.now()
        )

    def test_fail(
        self,
        logger,
        *args
    ):
        args[0].side_effect = ValueError('failed')
        loader._load_patient(self.patient, self.initial_patient_load)
        call_args = logger.error.call_args_list
        self.assertEqual(len(call_args), 1)
        err_msg = logger.error.call_args[0][0]
        self.assertIn(f'Initial patient load for patient id {self.patient.id} failed on load_appointments', err_msg)
        self.assertIn(f'ValueError: failed', err_msg)
        self.assertEqual(
            self.initial_patient_load.state, self.initial_patient_load.FAILURE
        )

    def test_results_fail(
        self,
        logger,
        *args
    ):
        args[-1].side_effect = ValueError('failed')
        loader._load_patient(self.patient, self.initial_patient_load)
        call_args = logger.error.call_args_list
        self.assertEqual(len(call_args), 1)
        err_msg = logger.error.call_args[0][0]
        self.assertIn(f'Initial patient load for patient id {self.patient.id} failed on results', err_msg)
        self.assertIn(f'ValueError: failed', err_msg)
        self.assertEqual(
            self.initial_patient_load.state, self.initial_patient_load.FAILURE
        )

    def test_success(self, logger, *args):
        loader._load_patient(self.patient, self.initial_patient_load)
        call_args_list = [i[0][0] for i in logger.info.call_args_list]
        expected = [
            f'Started patient {self.patient.id} Initial Load {self.initial_patient_load.id}',
            f'Loaded results for patient id {self.patient.id}',
            f'Tests updated for patient id {self.patient.id}',
            f'Completed update_patient_information for patient id {self.patient.id}',
            f'Completed load_imaging for patient id {self.patient.id}',
            f'Completed load_encounters for patient id {self.patient.id}',
            f'Completed load_appointments for patient id {self.patient.id}',
            f'Completed load_transfer_history_for_patient for patient id {self.patient.id}',
        ]
        self.assertEqual(
            call_args_list, expected
        )


class LogErrorsTestCase(ApiTestCase):
    @mock.patch.object(loader.logger, "error")
    def test_log_errors(self, err):
        loader.logger.error("blah")
        err.assert_called_once_with("blah")


class LoadDemographicsTestCase(ApiTestCase):

    @mock.patch.object(loader.api, 'demographics')
    def test_success(self, demographics):
        demographics.return_value = "success"
        result = loader.load_demographics("some_hospital_number")
        demographics.assert_called_once_with("some_hospital_number")
        self.assertEqual(result, "success")

    @mock.patch.object(loader.api, 'demographics')
    @mock.patch.object(loader.logger, 'info')
    @mock.patch('intrahospital_api.loader.log_errors')
    def test_failed(self, log_err, info, demographics):
        demographics.side_effect = ValueError("Boom")
        demographics.return_value = "success"
        loader.load_demographics("some_hospital_number")
        self.assertEqual(info.call_count, 1)
        log_err.assert_called_once_with("load_demographics")

    @override_settings(
        INTRAHOSPITAL_API='intrahospital_api.apis.dev_api.DevApi'
    )
    def test_integration(self):
        result = loader.load_demographics("some_number")
        self.assertTrue(isinstance(result, dict))


@mock.patch('intrahospital_api.loader.async_task')
@mock.patch('intrahospital_api.loader._load_patient')
class LoadLabTestsForPatientTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(LoadLabTestsForPatientTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()

    @override_settings(ASYNC_API=True)
    def test_load_patient_arg_override_settings_True(
        self, load_lab_tests, _async
    ):
        loader.load_patient(self.patient, run_async=False)
        self.assertTrue(load_lab_tests.called)
        self.assertFalse(_async.called)

    @override_settings(ASYNC_API=False)
    def test_load_patient_arg_override_settings_False(
        self, load_lab_tests, _async
    ):
        loader.load_patient(self.patient, run_async=True)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(_async.called)

    @override_settings(ASYNC_API=True)
    def test_load_patient_arg_override_settings_None_True(
        self, load_lab_tests, _async
    ):
        loader.load_patient(self.patient)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(_async.called)

    @override_settings(ASYNC_API=False)
    def test_load_patient_arg_override_settings_None_False(
        self, load_lab_tests, _async
    ):
        loader.load_patient(self.patient)
        self.assertTrue(load_lab_tests.called)
        self.assertFalse(_async.called)

    def test_load_patient_async(
        self, load_lab_tests, _async
    ):
        loader.load_patient(self.patient, run_async=True)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(_async.called)
        call_args_list = _async.call_args_list
        self.assertEqual(call_args_list[0][0][0], self.patient)
        patient_load = call_args_list[0][0][1]
        self.assertTrue(
            isinstance(patient_load, imodels.InitialPatientLoad)
        )
        self.assertIsNone(patient_load.stopped)
        self.assertIsNotNone(patient_load.started)

    def test_load_patient_async_false(
        self, load_lab_tests, _async
    ):
        loader.load_patient(self.patient, run_async=False)
        self.assertFalse(_async.called)
        self.assertTrue(load_lab_tests.called)
        call_args_list = load_lab_tests.call_args_list
        self.assertEqual(call_args_list[0][0][0], self.patient)
        patient_load = call_args_list[0][0][1]
        self.assertTrue(
            isinstance(patient_load, imodels.InitialPatientLoad)
        )
        self.assertIsNone(patient_load.stopped)
        self.assertIsNotNone(patient_load.started)


@mock.patch('intrahospital_api.tasks.load.delay')
@mock.patch('intrahospital_api.loader.transaction')
class AsyncTaskTestCase(ApiTestCase):
    def test_async_task(self, transaction, delay):
        patient, _ = self.new_patient_and_episode_please()
        patient_load = imodels.InitialPatientLoad.objects.create(
            patient=patient,
            started=timezone.now()
        )
        loader.async_task(patient, patient_load)
        call_args = transaction.on_commit.call_args
        call_args[0][0]()
        delay.assert_called_once_with(patient.id, patient_load.id)


@mock.patch('intrahospital_api.loader.log_errors')
@mock.patch('intrahospital_api.loader._load_patient')
class AsyncLoadPatientTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        # additional patient so that they have different ids
        # so we can confirm ordering
        patient, _ = self.new_patient_and_episode_please()
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient_load = imodels.InitialPatientLoad.objects.create(
            patient=patient,
            started=timezone.now()
        )

    def test_success(self, load_patient, log_errors):
        loader.async_load_patient(self.patient.id, self.patient_load.id)
        self.assertFalse(log_errors.called)
        load_patient.assert_called_once_with(self.patient, self.patient_load)

    def test_raise(self, load_patient, log_errors):
        load_patient.side_effect = ValueError('Boom')
        with self.assertRaises(ValueError) as ve:
            loader.async_load_patient(self.patient.id, self.patient_load.id)

        log_errors.assert_called_once_with("_load_patient")
        self.assertEqual(str(ve.exception), "Boom")


class UpdatePatientFromBatchTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(UpdatePatientFromBatchTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        demographics = self.patient.demographics_set.first()
        demographics.hospital_number = "123"
        demographics.save()
        lt = lab_test_models.LabTest.objects.create(
            patient=self.patient,
            lab_number="234",
            test_name="some_test"
        )
        lab_test_models.Observation.objects.create(
            observation_number="345",
            observation_value="Pending",
            test=lt
        )

        self.data_deltas = {
            "demographics": {
                "hospital_number": "123",
                "first_name": "Jane"
            },
            "lab_tests": [{
                "external_identifier": "234",
                "test_name": "some_test",
                "test_code": "AN12",
                "clinical_info":  'testing',
                "datetime_ordered": "17/07/2015 04:15:10",
                "site": u'^&        ^',
                "status": "Sucess",
                "observations": [{
                    "last_updated": "18/07/2015 04:15:10",
                    "observation_datetime": "19/07/2015 04:15:10",
                    "observation_name": "Aerobic bottle culture",
                    "observation_number": "345",
                    "observation_value": "Positive",
                    "reference_range": "3.5 - 11",
                }],
            }]
        }


class SynchAllPatientsTestCase(ApiTestCase):
    @mock.patch('intrahospital_api.loader.sync_patient')
    @mock.patch.object(loader.logger, 'info')
    def test_sync_all_patients(self, info, sync_patient):
        p, _ = self.new_patient_and_episode_please()
        loader.sync_all_patients()

        info.assert_called_once_with("Synching {} (1/1)".format(
            p.id
        ))
        sync_patient.assert_called_once_with(p)

    @mock.patch('intrahospital_api.loader.sync_patient')
    @mock.patch('intrahospital_api.loader.log_errors')
    @mock.patch.object(loader.logger, 'info')
    def test_sync_all_patients_with_error(self, info, log_errors, sync_patient):
        sync_patient.side_effect = ValueError('Boom')
        patient, _ = self.new_patient_and_episode_please()
        loader.sync_all_patients()
        log_errors.assert_called_once_with(
            "Unable to sync {}".format(patient.id)
        )


class SynchPatientTestCase(ApiTestCase):
    @mock.patch.object(loader.logger, 'info')
    @mock.patch.object(loader.api, 'results_for_hospital_number')
    @mock.patch('intrahospital_api.loader.update_lab_tests.update_tests')
    @mock.patch(
        'intrahospital_api.loader.update_demographics.update_patient_information'
    )
    def test_synch_patient(
        self, update_patient_information, update_tests, results, info
    ):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="111"
        )
        results.return_value = "some_results"
        loader.sync_patient(patient)
        results.assert_called_once_with('111')
        update_tests.assert_called_once_with(patient, "some_results")
        update_patient_information.assert_called_once_with(patient)
        self.assertEqual(
            info.call_args_list[0][0][0],
            "fetched results for patient {}".format(patient.id)
        )
        self.assertEqual(
            info.call_args_list[1][0][0],
            "tests synced for {}".format(patient.id)
        )
        self.assertEqual(
            info.call_args_list[2][0][0],
            "patient information synced for {}".format(patient.id)
        )


class CreateRfhPatientFromHospitalNumberTestCase(OpalTestCase):
    def test_creates_patient_and_episode(self):
        patient = loader.create_rfh_patient_from_hospital_number(
            '111', episode_categories.InfectionService
        )
        self.assertEqual(
            patient.demographics_set.get().hospital_number, '111'
        )
        self.assertEqual(
            patient.episode_set.get().category_name,
            episode_categories.InfectionService.display_name
        )

    def test_errors_if_the_hospital_number_starts_with_a_zero(self):
        with self.assertRaises(ValueError) as v:
            loader.create_rfh_patient_from_hospital_number(
                '0111', episode_categories.InfectionService
            )
        expected = " ".join([
            "Unable to create a patient 0111.",
            "Hospital numbers within elCID should never start with a zero"
        ])
        self.assertEqual(str(v.exception), expected)
