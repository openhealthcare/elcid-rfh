import mock
import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import override_settings
from opal import models as opal_models
from opal.core.test import OpalTestCase
from elcid import models as emodels
from intrahospital_api import models as imodels
from intrahospital_api import loader
from intrahospital_api.test.core import ApiTestCase
from intrahospital_api.exceptions import BatchLoadError
from intrahospital_api.constants import EXTERNAL_SYSTEM



class InitialLoadTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(InitialLoadTestCase, self).setUp(*args, **kwargs)

        # the first two patients should be updated, but not the last
        self.patient_1, _ = self.new_patient_and_episode_please()
        self.patient_2, _ = self.new_patient_and_episode_please()
        self.patient_3, _ = self.new_patient_and_episode_please()
        emodels.Demographics.objects.filter(
            patient__in=[self.patient_1, self.patient_2]
        ).update(external_system=EXTERNAL_SYSTEM)

    @mock.patch("intrahospital_api.loader.log_errors")
    def test_deletes_existing(self, log_errors):
        patient, _ = self.new_patient_and_episode_please()
        pk = imodels.InitialPatientLoad.objects.create(
            patient=patient, started=timezone.now()
        ).pk

        loader.initial_load()

        self.assertFalse(
            imodels.InitialPatientLoad.objects.filter(id=pk).exists()
        )


    @mock.patch(
        "intrahospital_api.loader.demographics_service.load_patient",
    )
    @mock.patch(
        "intrahospital_api.loader.lab_tests_service.refresh_patient",
    )
    @mock.patch(
        "intrahospital_api.loader.appointments_service.refresh_patient",
    )
    def test_flow(
        self, refresh_appointments, refresh_patient_lab_tests, load_patient
    ):
        with mock.patch.object(loader.logger, "info") as info:
            loader.initial_load()
            self.assertEqual(
                refresh_appointments.call_count, 3
            )
            self.assertEqual(
                load_patient.call_count, 3
            )
            self.assertEqual(
                refresh_patient_lab_tests.call_count, 3
            )
            call_args_list = info.call_args_list

            expected_log_messages = [
                "running 1/3",
                "starting to load patient 1",
                'loading patient 1 synchronously',
                'started patient 1 ipl 1',
                "running 2/3",
                "starting to load patient 2",
                'loading patient 2 synchronously',
                'started patient 2 ipl 2',
                "running 3/3",
                "starting to load patient 3",
                'loading patient 3 synchronously',
            ]

            for idx, expected_log_message in enumerate(expected_log_messages):
                self.assertEqual(
                    call_args_list[idx][0][0], expected_log_message
                )


@mock.patch('intrahospital_api.loader.async_task')
@mock.patch('intrahospital_api.loader._load_patient')
class LoadLabTestsForPatientTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(LoadLabTestsForPatientTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()

    @override_settings(ASYNC_API=True)
    def test_load_patient_arg_override_settings_True(
        self, load_lab_tests, run_async
    ):
        loader.load_patient(self.patient, run_async=False)
        self.assertTrue(load_lab_tests.called)
        self.assertFalse(run_async.called)

    @override_settings(ASYNC_API=False)
    def test_load_patient_arg_override_settings_False(
        self, load_lab_tests, run_async
    ):
        loader.load_patient(self.patient, run_async=True)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(run_async.called)

    @override_settings(ASYNC_API=True)
    def test_load_patient_arg_override_settings_None_True(
        self, load_lab_tests, run_async
    ):
        loader.load_patient(self.patient)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(run_async.called)

    @override_settings(ASYNC_API=False)
    def test_load_patient_arg_override_settings_None_False(
        self, load_lab_tests, run_async
    ):
        loader.load_patient(self.patient)
        self.assertTrue(load_lab_tests.called)
        self.assertFalse(run_async.called)

    def test_load_patient_async(
        self, load_lab_tests, run_async
    ):
        loader.load_patient(self.patient, run_async=True)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(run_async.called)
        call_args_list = run_async.call_args_list
        self.assertEqual(call_args_list[0][0][0], self.patient)
        patient_load = call_args_list[0][0][1]
        self.assertTrue(
            isinstance(patient_load, imodels.InitialPatientLoad)
        )
        self.assertIsNone(patient_load.stopped)
        self.assertIsNotNone(patient_load.started)

    def test_load_patient_async_false(
        self, load_lab_tests, run_async
    ):
        loader.load_patient(self.patient, run_async=False)
        self.assertFalse(run_async.called)
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


class LogErrorTestCase(OpalTestCase):
    def test_log_error(self):
        with mock.patch.object(loader.logger, "error") as le:
            loader.log_errors("boom")
        le.assert_called_once_with('unable to run boom \n None\n')


@override_settings(API_STATE="dev")
class QueryPatientDemographicsTestCase(OpalTestCase):
    def test_query_patient_demographics(self):
        result = loader.query_patient_demographics("111")
        self.assertEqual(
            result["hospital_number"], "111"
        )

    @mock.patch("intrahospital_api.loader.service_utils.get_api")
    @mock.patch("intrahospital_api.loader.log_errors")
    def test_query_patient_demographics_error(self, log_errors, get_api):
        api = get_api.return_value
        api.demographics_for_hospital_number.side_effect = ValueError("Boom")
        result = loader.query_patient_demographics("111")
        self.assertIsNone(result)
        err = log_errors.assert_called_once_with("query_patient_demographics")
