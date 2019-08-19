import mock
import datetime
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from opal.core.test import OpalTestCase
from elcid import models as emodels
from intrahospital_api import models as imodels
from intrahospital_api import loader
from intrahospital_api.exceptions import BatchLoadError
from intrahospital_api.constants import EXTERNAL_SYSTEM
from plugins.labtests import models as lab_test_models


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
        "intrahospital_api.loader.update_demographics.reconcile_all_demographics",
    )
    @mock.patch(
        "intrahospital_api.loader.load_patient",
    )
    def test_flow(self, load_patient, reconcile_all_demographics):
        with mock.patch.object(loader.logger, "info") as info:
            loader._initial_load()
            reconcile_all_demographics.assert_called_once_with()
            call_args_list = load_patient.call_args_list
            self.assertEqual(
                call_args_list[0][0], (self.patient_1,)
            )
            self.assertEqual(
                call_args_list[0][1], dict(run_async=False)
            )
            self.assertEqual(
                call_args_list[1][0], (self.patient_2,)
            )
            self.assertEqual(
                call_args_list[1][1], dict(run_async=False)
            )
            call_args_list = info.call_args_list
            self.assertEqual(
                call_args_list[0][0], ("running 1/2",)
            )
            self.assertEqual(
                call_args_list[1][0], ("running 2/2",)
            )

    @override_settings(
        INTRAHOSPITAL_API='intrahospital_api.apis.dev_api.DevApi'
    )
    def test_integration(self):
        with mock.patch.object(loader.logger, "info"):
            loader._initial_load()

            self.assertIsNotNone(
                self.patient_1.demographics_set.first().hospital_number
            )

            self.assertIsNotNone(
                self.patient_2.demographics_set.first().hospital_number
            )

            self.assertEqual(
                imodels.InitialPatientLoad.objects.first().patient.id,
                self.patient_1.id
            )
            self.assertEqual(
                imodels.InitialPatientLoad.objects.last().patient.id,
                self.patient_2.id
            )
            upstream_patients = lab_test_models.LabTest.objects.values_list(
                "patient_id", flat=True
            ).distinct()
            self.assertEqual(
                set([self.patient_1.id, self.patient_2.id]),
                set(upstream_patients)
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
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient, run_async=False)
        self.assertTrue(load_lab_tests.called)
        self.assertFalse(async.called)

    @override_settings(ASYNC_API=False)
    def test_load_patient_arg_override_settings_False(
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient, run_async=True)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(async.called)

    @override_settings(ASYNC_API=True)
    def test_load_patient_arg_override_settings_None_True(
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(async.called)

    @override_settings(ASYNC_API=False)
    def test_load_patient_arg_override_settings_None_False(
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient)
        self.assertTrue(load_lab_tests.called)
        self.assertFalse(async.called)

    def test_load_patient_async(
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient, run_async=True)
        self.assertFalse(load_lab_tests.called)
        self.assertTrue(async.called)
        call_args_list = async.call_args_list
        self.assertEqual(call_args_list[0][0][0], self.patient)
        patient_load = call_args_list[0][0][1]
        self.assertTrue(
            isinstance(patient_load, imodels.InitialPatientLoad)
        )
        self.assertIsNone(patient_load.stopped)
        self.assertIsNotNone(patient_load.started)

    def test_load_patient_async_false(
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient, run_async=False)
        self.assertFalse(async.called)
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
            "Last load is still running and has been for 600.0 mins"
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
    @mock.patch.object(loader.api, "data_deltas")
    @mock.patch('intrahospital_api.loader.update_demographics.reconcile_all_demographics')
    @mock.patch('intrahospital_api.loader.update_from_batch')
    def test_batch_load(
        self, update_from_batch, reconcile_all_demographics, data_deltas
    ):
        now = timezone.now()
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=now
        )
        data_deltas.return_value = "something"
        loader._batch_load()
        reconcile_all_demographics.assert_called_once_with()
        data_deltas.assert_called_once_with(now)
        update_from_batch.assert_called_once_with("something")


@mock.patch('intrahospital_api.loader.update_patient_from_batch')
class UpdateFromBatchTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(UpdateFromBatchTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        self.demographics = self.patient.demographics_set.first()
        self.demographics.external_system = EXTERNAL_SYSTEM
        self.demographics.save()
        self.initial_load = imodels.InitialPatientLoad.objects.create(
            patient=self.patient,
            started=timezone.now(),
            stopped=timezone.now(),
            state=imodels.InitialPatientLoad.SUCCESS
        )
        self.data_delta = dict(some="data")
        self.data_deltas = [self.data_delta]

    def test_update_from_batch_ignore_non_reconciled(
        self, update_patient_from_batch
    ):
        self.demographics.external_system = "asdfasfd"
        self.demographics.save()
        loader.update_from_batch(self.data_deltas)
        call_args = update_patient_from_batch.call_args
        self.assertEqual(
            list(call_args[0][0]), list()
        )
        self.assertEqual(
            call_args[0][1], self.data_delta
        )

    def test_update_from_batch_ignore_failed_loads(
        self, update_patient_from_batch
    ):
        self.initial_load.state = imodels.InitialPatientLoad.FAILURE
        self.initial_load.save()
        loader.update_from_batch(self.data_deltas)
        call_args = update_patient_from_batch.call_args
        self.assertEqual(
            list(call_args[0][0]), list()
        )
        self.assertEqual(
            call_args[0][1], self.data_delta
        )

    def test_update_from_batch_pass_through(
        self, update_patient_from_batch
    ):
        loader.update_from_batch(self.data_deltas)
        call_args = update_patient_from_batch.call_args
        self.assertEqual(
            list(call_args[0][0]), [self.demographics]
        )
        self.assertEqual(
            call_args[0][1], self.data_delta
        )


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

    def test_update_patient_from_batch_integration(self):
        loader.update_patient_from_batch(
            emodels.Demographics.objects.all(),
            self.data_deltas
        )
        self.assertEqual(
            self.patient.demographics_set.first().first_name, "Jane"
        )
        obs = self.patient.lab_tests.get().observation_set.first()
        self.assertEqual(
            obs.observation_value, "Positive"
        )


class AnyLoadsRunningTestCase(ApiTestCase):
    def test_any_loads_running_initial_patient_load(self):
        patient, _ = self.new_patient_and_episode_please()
        imodels.InitialPatientLoad.objects.create(
            state=imodels.InitialPatientLoad.RUNNING,
            patient=patient,
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
        patient, _ = self.new_patient_and_episode_please()
        imodels.InitialPatientLoad.objects.create(
            state=imodels.InitialPatientLoad.SUCCESS,
            patient=patient,
            started=timezone.now()
        )
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=timezone.now()
        )
        self.assertFalse(loader.any_loads_running())
