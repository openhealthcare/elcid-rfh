import mock
import copy
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


@override_settings(API_USER="ohc")
class ApiTestCase(OpalTestCase):
    def setUp(self):
        super(ApiTestCase, self).setUp()
        User.objects.create(username="ohc", password="fake_password")


@mock.patch("intrahospital_api.loader._initial_load")
@mock.patch("intrahospital_api.loader.logger")
class InitialLoadTestCase(ApiTestCase):
    def test_successful_load(self, logger, _initial_load):
        loader.initial_load()
        _initial_load.assert_called_once_with()
        self.assertFalse(logger.error.called)
        batch_load = imodels.BatchPatientLoad.objects.get()
        self.assertEqual(batch_load.state, batch_load.SUCCESS)
        self.assertTrue(batch_load.started < batch_load.stopped)

    def test_failed_load(self, logger, _initial_load):
        _initial_load.side_effect = ValueError("Boom")
        with self.assertRaises(ValueError):
            loader.initial_load()
        _initial_load.assert_called_once_with()
        logger.error.assert_called_once_with("Unable to run initial_load")
        batch_load = imodels.BatchPatientLoad.objects.get()
        self.assertEqual(batch_load.state, batch_load.FAILURE)
        self.assertTrue(batch_load.started < batch_load.stopped)

    def test_deletes_existing(self, logger, _initial_load):
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
        with mock.patch("intrahospital_api.loader.logger.info") as info:
            loader._initial_load()
            reconcile_all_demographics.assert_called_once_with()
            call_args_list = load_patient.call_args_list
            self.assertEqual(
                call_args_list[0][0], (self.patient_1,)
            )
            self.assertEqual(
                call_args_list[0][1], dict(async=False)
            )
            self.assertEqual(
                call_args_list[1][0], (self.patient_2,)
            )
            self.assertEqual(
                call_args_list[1][1], dict(async=False)
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
        with mock.patch("intrahospital_api.loader.logger.info"):
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

            upstream_patients = emodels.UpstreamLabTest.objects.values_list(
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


class LoadDemographicsTestCase(ApiTestCase):

    @mock.patch.object(loader.api, 'demographics')
    def test_success(self, demographics):
        demographics.return_value = "success"
        result = loader.load_demographics("some_hospital_number")
        demographics.assert_called_once_with("some_hospital_number")
        self.assertEqual(result, "success")

    @mock.patch.object(loader.api, 'demographics')
    @mock.patch('intrahospital_api.loader.logger')
    def test_failed(self, logger, demographics):
        demographics.side_effect = ValueError("Boom")
        demographics.return_value = "success"
        loader.load_demographics("some_hospital_number")
        self.assertEqual(logger.info.call_count, 1)
        logger.error.assert_called_once_with("Unable to run load_demographics")

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

    def test_cancel_running_initial_patient_loads(
        self, load_lab_tests, async
    ):
        ipl = imodels.InitialPatientLoad(patient=self.patient)
        ipl.start()
        loader.load_patient(self.patient, async=False)
        self.assertTrue(
            imodels.InitialPatientLoad.objects.get(id=ipl.id).state,
            imodels.InitialPatientLoad.CANCELLED
        )

    @override_settings(ASYNC_API=True)
    def test_load_patient_arg_override_settings_True(
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient, async=False)
        self.assertTrue(load_lab_tests.called)
        self.assertFalse(async.called)

    @override_settings(ASYNC_API=False)
    def test_load_patient_arg_override_settings_False(
        self, load_lab_tests, async
    ):
        loader.load_patient(self.patient, async=True)
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
        loader.load_patient(self.patient, async=True)
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
        loader.load_patient(self.patient, async=False)
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
class AsyncTaskTestCase(ApiTestCase):
    def test_async_task(self, delay):
        patient, _ = self.new_patient_and_episode_please()
        patient_load = imodels.InitialPatientLoad.objects.create(
            patient=patient,
            started=timezone.now()
        )
        loader.async_task(patient, patient_load)
        delay.assert_called_once_with(patient, patient_load)


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

    @mock.patch('intrahospital_api.loader.logger.info')
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

    @mock.patch('intrahospital_api.loader.logger.info')
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
            started=timezone    .now() - delta,
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


@mock.patch("intrahospital_api.loader.logger")
class CheckForLongRunningInitialPatientLoadsTestCase(ApiTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def create_ipl(self, state, started=None, stopped=None):
        ipl = imodels.InitialPatientLoad(patient=self.patient)
        ipl.state = state
        ipl.started = started
        ipl.stopped = stopped
        ipl.save()

    def test_long_running_ipl_found(self, logger):
        four_hours_ago = timezone.now() - datetime.timedelta(hours=4)
        self.create_ipl(
            imodels.InitialPatientLoad.RUNNING,
            started=four_hours_ago
        )
        loader.check_for_long_running_initial_patient_loads()
        logger.error.assert_called_once_with(
            "We have long running initial patient loads"
        )

    def test_no_ipls(self, logger):
        loader.check_for_long_running_initial_patient_loads()
        self.assertFalse(logger.error.called)

    def test_recent_ipl_finished(self, logger):
        recent_start = timezone.now() - datetime.timedelta(seconds=200)
        recent_stop = timezone.now() - datetime.timedelta(seconds=100)
        state = imodels.InitialPatientLoad.SUCCESS
        self.create_ipl(
            state,
            started=recent_start,
            stopped=recent_stop
        )
        loader.check_for_long_running_initial_patient_loads()
        self.assertFalse(logger.error.called)

    def test_long_running_ipl_cancelled(self, logger):
        four_hours_ago = timezone.now() - datetime.timedelta(hours=4)
        self.create_ipl(
            imodels.InitialPatientLoad.CANCELLED,
            started=four_hours_ago
        )
        loader.check_for_long_running_initial_patient_loads()
        self.assertFalse(logger.error.called)


@mock.patch("intrahospital_api.loader.logger")
@mock.patch("intrahospital_api.loader._batch_load")
@mock.patch("intrahospital_api.loader.good_to_go")
class BatchLoadTestCase(ApiTestCase):
    def test_with_force(self, good_to_go, _batch_load, logger):
        loader.batch_load(force=True)
        good_to_go.return_value = True
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.SUCCESS)
        self.assertFalse(good_to_go.called)
        self.assertTrue(_batch_load.called)

    def test_without_force_not_good_to_go(
        self, good_to_go, _batch_load,logger
    ):
        good_to_go.return_value = False
        loader.batch_load()
        self.assertTrue(good_to_go.called)
        self.assertFalse(_batch_load.called)
        self.assertFalse(imodels.BatchPatientLoad.objects.exists())

    def test_without_force_good_to_go(self, good_to_go, _batch_load, logger):
        loader.batch_load()
        good_to_go.return_value = True
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.SUCCESS)
        self.assertTrue(good_to_go.called)
        self.assertTrue(_batch_load.called)

    def test_with_error(self, good_to_go, _batch_load, logger):
        _batch_load.side_effect = ValueError("Boom")
        loader.batch_load()
        good_to_go.return_value = True
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.FAILURE)
        self.assertTrue(good_to_go.called)
        self.assertTrue(_batch_load.called)
        logger.error.assert_called_once_with("Unable to run batch load")


class _BatchLoadTestCase(ApiTestCase):
    @mock.patch.object(loader.api, "data_deltas")
    @mock.patch(
        'intrahospital_api.loader.update_demographics.reconcile_all_demographics'
    )
    @mock.patch('intrahospital_api.loader.update_from_batch')
    def test_batch_load(
        self, update_from_batch, reconcile_all_demographics, data_deltas
    ):
        now = timezone.now()
        batch_load = imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=now
        )
        data_deltas_dict = [dict(
            demographcis=dict(hospital_number="1"),
            lab_tests=[dict(external_identifier="123")]
        )]
        data_deltas.return_value = data_deltas_dict
        loader._batch_load(batch_load)
        reconcile_all_demographics.assert_called_once_with()
        data_deltas.assert_called_once_with(now)
        update_from_batch.assert_called_once_with(data_deltas_dict)
        self.assertEqual(batch_load.count, 1)


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
        emodels.UpstreamLabTest.objects.create(
            patient=self.patient,
            external_identifier="234",
            extras=dict(
                observations=[{
                    "observation_number": "345",
                    "result": "Pending"
                }],
                test_name="some_test"
            )
        )
        self.data_deltas = {
            "demographics": {
                "hospital_number": "123",
                "first_name": "Jane",
                "nhs_number": "345"
            },
            "lab_tests": [{
                "external_identifier": "234",
                "test_name": "some_test",
                "observations": [{
                    "observation_number": "345",
                    "result": "Positive"
                }]
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
        observation = self.patient.labtest_set.first().extras[
            "observations"
        ][0]
        self.assertEqual(
            observation["result"], "Positive"
        )

    def test_update_patient_from_batch_integration_nhs_number(self):
        self.patient.demographics_set.update(nhs_number="345")
        data_deltas = copy.copy(self.data_deltas)
        data_deltas["demographics"]["hospital_number"] = ""
        loader.update_patient_from_batch(
            emodels.Demographics.objects.all(),
            data_deltas
        )
        self.assertEqual(
            self.patient.demographics_set.first().first_name, "Jane"
        )
        observation = self.patient.labtest_set.first().extras[
            "observations"
        ][0]
        self.assertEqual(
            observation["result"], "Positive"
        )


@mock.patch("intrahospital_api.loader.api")
class _LoadPatientTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(_LoadPatientTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        self.ipl = imodels.InitialPatientLoad(patient=self.patient)
        self.ipl.start()
        self.demographics = {
            "hospital_number": "123",
            "first_name": "Jane"
        }

        self.lab_tests = [{
            "external_identifier": "234",
            "test_name": "some_test",
            "observations": [{
                "observation_number": "345",
                "result": "Positive"
            }]
        }]

    def test_success(self, api):
        api.results_for_hospital_number.return_value = self.lab_tests
        api.demographics.return_value = self.demographics
        loader._load_patient(self.patient, self.ipl)
        demographics = self.patient.demographics_set.first()
        self.assertEqual(
            demographics.first_name, "Jane"
        )
        self.assertEqual(
            demographics.hospital_number, "123"
        )
        lab_test = self.patient.labtest_set.get()
        self.assertEqual(
            lab_test.external_identifier, "234"
        )
        self.assertEqual(self.ipl.state, self.ipl.SUCCESS)
        self.assertTrue(bool(self.ipl.started))
        self.assertTrue(bool(self.ipl.stopped))
        self.assertEqual(
            self.ipl.count, 1
        )

    @mock.patch("intrahospital_api.loader.update_demographics")
    @mock.patch("intrahospital_api.loader.logger")
    def test_fail(self, logger, update_demographics, api):
        upd = update_demographics.update_patient_demographics
        upd.side_effect = ValueError("Boom")
        with self.assertRaises(ValueError):
            loader._load_patient(self.patient, self.ipl)
        self.assertTrue(logger.info.called)
        self.assertEqual(self.ipl.state, self.ipl.FAILURE)
        self.assertTrue(bool(self.ipl.started))
        self.assertTrue(bool(self.ipl.stopped))
        self.assertEqual(
            self.ipl.count, 0
        )


@mock.patch("intrahospital_api.loader._load_patient")
@mock.patch("intrahospital_api.loader.logger")
class AsyncLoadPatientTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        self.patient, _ = self.new_patient_and_episode_please()
        self.ipl = imodels.InitialPatientLoad(patient=self.patient)
        self.ipl.start()

    def test_async_load_patient_success(self, logger, _load_patient):
        loader.async_load_patient(self.patient.id, self.ipl.id)
        _load_patient.assert_called_once_with(self.patient, self.ipl)
        self.assertFalse(logger.error.called)

    def test_async_load_patient_error(self, logger, _load_patient):
        _load_patient.side_effect = ValueError('Boom')

        with self.assertRaises(ValueError):
            loader.async_load_patient(self.patient.id, self.ipl.id)
        _load_patient.assert_called_once_with(self.patient, self.ipl)
        logger.error.assert_called_once_with("Unable to run _load_patient")
