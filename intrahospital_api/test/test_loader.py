import mock
import datetime
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from opal.core.test import OpalTestCase
from opal import models as opal_models
from elcid import models as emodels
from intrahospital_api import models as imodels
from intrahospital_api import loader
from intrahospital_api.exceptions import BatchLoadError
from intrahospital_api.constants import EXTERNAL_SYSTEM


@override_settings(API_USER="ohc")
class ApiTestCase(OpalTestCase):
    def setUp(self):
        super(ApiTestCase, self).setUp()
        User.objects.create(username="ohc", password="fake_password")


@mock.patch("intrahospital_api.loader._initial_load")
@mock.patch("intrahospital_api.loader.log_errors")
class InitialLoadTestCase(ApiTestCase):
    def test_successful_load(self, log_errors, _initial_load):
        loader.initial_load()
        _initial_load.assert_called_once_with()
        self.assertFalse(log_errors.called)
        batch_load = imodels.BatchPatientLoad.objects.get()
        self.assertEqual(batch_load.state, batch_load.SUCCESS)
        self.assertTrue(batch_load.started < batch_load.stopped)

    def test_failed_load(self, log_errors, _initial_load):
        _initial_load.side_effect = ValueError("Boom")
        with self.assertRaises(ValueError):
            loader.initial_load()
        _initial_load.assert_called_once_with()
        log_errors.assert_called_once_with("initial_load")
        batch_load = imodels.BatchPatientLoad.objects.get()
        self.assertEqual(batch_load.state, batch_load.FAILURE)
        self.assertTrue(batch_load.started < batch_load.stopped)

    def test_deletes_existing(self, log_errors, _initial_load):
        patient, _ = self.new_patient_and_episode_please()
        imodels.InitialPatientLoad.objects.create(
            patient=patient, started=timezone.now()
        )
        previous_load = imodels.BatchPatientLoad.objects.create(
            started=timezone.now()
        )
        loader.initial_load()
        self.assertNotEqual(
            previous_load.id, imodels.BatchPatientLoad.objects.first().id
        )

        self.assertFalse(
            imodels.InitialPatientLoad.objects.exists()
        )


class _InitialLoadTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(_InitialLoadTestCase, self).setUp(*args, **kwargs)

        # the first two patients should be updated, but not the last
        self.patient_1, _ = self.new_patient_and_episode_please()
        self.patient_2, _ = self.new_patient_and_episode_please()
        self.patient_3, _ = self.new_patient_and_episode_please()
        emodels.Demographics.objects.filter(
            patient__in=[self.patient_1, self.patient_2]
        ).update(external_system=EXTERNAL_SYSTEM)

    @mock.patch(
        "intrahospital_api.loader.demographics.sync_patient_demographics",
    )
    @mock.patch(
        "intrahospital_api.loader.lab_tests.refresh_patient_lab_tests",
    )
    def test_flow(self, refresh_patient_lab_tests, sync_patient_demographics):
        with mock.patch.object(loader.logger, "info") as info:
            loader._initial_load()
            self.assertEqual(
                sync_patient_demographics.call_count, 3
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


class GetBatchStartTime(ApiTestCase):
    def test_batch_load_first(self):
        now = timezone.now()
        batch_start = now - datetime.timedelta(minutes=1)
        imodels.BatchPatientLoad.objects.create(
            started=batch_start,
            stopped=now,
            state=imodels.BatchPatientLoad.SUCCESS
        )
        self.assertEqual(
            loader.get_batch_start_time(),
            batch_start
        )

    def test_initial_patient_load_first(self):
        now = timezone.now()
        batch_start = now - datetime.timedelta(minutes=2)
        initial_patient_load_start = now - datetime.timedelta(minutes=3)
        initial_patient_load_stop = now - datetime.timedelta(minutes=1)
        patient, _ = self.new_patient_and_episode_please()

        imodels.BatchPatientLoad.objects.create(
            started=batch_start,
            stopped=now,
            state=imodels.BatchPatientLoad.SUCCESS
        )

        imodels.InitialPatientLoad.objects.create(
            started=initial_patient_load_start,
            stopped=initial_patient_load_stop,
            state=imodels.InitialPatientLoad.SUCCESS,
            patient=patient
        )
        self.assertEqual(
            loader.get_batch_start_time(),
            initial_patient_load_start
        )


class AnyLoadsRunningTestCase(ApiTestCase):
    def setUp(self):
        super(AnyLoadsRunningTestCase, self).setUp()
        self.patient, _ = self.new_patient_and_episode_please()

    def test_any_loads_running_initial_patient_load(self):
        imodels.InitialPatientLoad.objects.create(
            state=imodels.InitialPatientLoad.RUNNING,
            patient=self.patient,
            started=timezone.now()
        )
        self.assertTrue(loader.any_loads_running())

    def test_any_loads_running_batch_patient_load(self):
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now()
        )
        self.assertTrue(loader.any_loads_running())

    def test_any_loads_running_none(self):
        self.assertFalse(loader.any_loads_running())

    def test_any_loads_running_false(self):
        imodels.InitialPatientLoad.objects.create(
            state=imodels.InitialPatientLoad.SUCCESS,
            patient=self.patient,
            started=timezone.now()
        )
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=timezone.now()
        )
        self.assertFalse(loader.any_loads_running())


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


class GoodToGoTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        self.patient, _ = self.new_patient_and_episode_please()
        super(GoodToGoTestCase, self).setUp(*args, **kwargs)

    def test_no_initial_batch_load(self):
        with self.assertRaises(BatchLoadError) as ble:
            loader.good_to_go()
        self.assertEqual(
            str(ble.exception),
            "We don't appear to have had an initial load run!"
        )

    def test_multiple_running(self):
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now()
        )
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now()
        )
        with self.assertRaises(BatchLoadError) as ble:
            loader.good_to_go()
        self.assertEqual(
            str(ble.exception),
            "We appear to have 2 concurrent batch loads"
        )

    @mock.patch.object(loader.logger, 'info')
    def test_last_load_running_less_than_ten_minutes(self, info):
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now(),
            stopped=timezone.now()
        )
        self.assertFalse(loader.good_to_go())
        info.assert_called_once_with(
            "batch still running after 0 seconds, skipping"
        )

    @mock.patch.object(loader.logger, 'info')
    def test_load_load_running_over_ten_minutes_first(self, info):
        diff = 100000
        delta = datetime.timedelta(seconds=diff)
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now() - delta,
            stopped=timezone.now() - delta
        )
        self.assertFalse(loader.good_to_go())

    def test_last_load_running_over_ten_minutes_not_first(self):
        diff = 60 * 60 * 10
        delta = datetime.timedelta(seconds=diff)

        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=timezone.now() - delta + datetime.timedelta(1),
            stopped=timezone.now() - delta + datetime.timedelta(1)
        )

        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now() - delta,
            stopped=timezone.now() - delta
        )

        with self.assertRaises(BatchLoadError) as ble:
            loader.good_to_go()
        self.assertEqual(
            str(ble.exception),
            "Last load is still running and has been for 600 mins"
        )

    def test_previous_run_has_not_happened_for_sometime(self):
        diff = 60 * 60 * 10
        delta = datetime.timedelta(seconds=diff)

        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=timezone.now() - delta,
            stopped=timezone.now() - delta
        )

        with self.assertRaises(BatchLoadError) as ble:
            loader.good_to_go()
        self.assertTrue(
            str(ble.exception).startswith("Last load has not run since")
        )


@mock.patch("intrahospital_api.loader.log_errors")
@mock.patch("intrahospital_api.loader._batch_load")
@mock.patch("intrahospital_api.loader.good_to_go")
class BatchLoadTestCase(ApiTestCase):
    def test_with_force(self, good_to_go, _batch_load, log_errors):
        loader.batch_load(force=True)
        good_to_go.return_value = True
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.SUCCESS)
        self.assertFalse(good_to_go.called)
        self.assertTrue(_batch_load.called)

    def test_without_force_not_good_to_go(self, good_to_go, _batch_load, log_errors):
        good_to_go.return_value = False
        loader.batch_load()
        self.assertTrue(good_to_go.called)
        self.assertFalse(_batch_load.called)
        self.assertFalse(imodels.BatchPatientLoad.objects.exists())

    def test_without_force_good_to_go(self, good_to_go, _batch_load, log_errors):
        loader.batch_load()
        good_to_go.return_value = True
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.SUCCESS)
        self.assertTrue(good_to_go.called)
        self.assertTrue(_batch_load.called)

    def test_with_error(self, good_to_go, _batch_load, log_errors):
        _batch_load.side_effect = ValueError("Boom")
        loader.batch_load()
        good_to_go.return_value = True
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.FAILURE)
        self.assertTrue(good_to_go.called)
        self.assertTrue(_batch_load.called)
        log_errors.assert_called_once_with("batch load")


class _BatchLoadTestCase(ApiTestCase):
    @mock.patch('intrahospital_api.loader.get_batch_start_time')
    @mock.patch('intrahospital_api.loader.lab_tests.update_lab_tests')
    def test_batch_load(
        self, update_lab_tests, get_batch_start_time
    ):
        now = timezone.now()
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=now
        )
        get_batch_start_time.return_value = now
        loader._batch_load()
        get_batch_start_time.assert_called_once_with()
        patient_loaded, _ = self.new_patient_and_episode_please()
        self.new_patient_and_episode_please()
        ipl = imodels.InitialPatientLoad(
            patient=patient_loaded
        )
        ipl.start()
        ipl.complete()
    
        self.assertEqual(
            update_lab_tests.call_args[0][0][0],
            patient_loaded
        )

        self.assertEqual(
            update_lab_tests.call_args[0][1],
            now
        )


