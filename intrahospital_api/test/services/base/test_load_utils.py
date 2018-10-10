import datetime
import mock
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api import models as imodels
from intrahospital_api.services.base import load_utils
from intrahospital_api.exceptions import BatchLoadError


class GetBatchStartTime(OpalTestCase):
    def test_batch_load_first(self):
        now = timezone.now()
        batch_start = now - datetime.timedelta(minutes=1)
        imodels.BatchPatientLoad.objects.create(
            started=batch_start,
            stopped=now,
            state=imodels.BatchPatientLoad.SUCCESS,
            service_name="test_service"
        )
        self.assertEqual(
            load_utils.get_batch_start_time("test_service"),
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
            state=imodels.BatchPatientLoad.SUCCESS,
            service_name="test_service"
        )

        imodels.InitialPatientLoad.objects.create(
            started=initial_patient_load_start,
            stopped=initial_patient_load_stop,
            state=imodels.InitialPatientLoad.SUCCESS,
            patient=patient,
        )
        self.assertEqual(
            load_utils.get_batch_start_time("test_service"),
            initial_patient_load_start
        )

    def test_looks_at_the_right_service(self):
        now = timezone.now()
        batch_start = now - datetime.timedelta(minutes=2)
        other_batch_start = now - datetime.timedelta(minutes=3)
        other_batch_stop = now - datetime.timedelta(minutes=1)
        patient, _ = self.new_patient_and_episode_please()

        imodels.BatchPatientLoad.objects.create(
            started=batch_start,
            stopped=now,
            state=imodels.BatchPatientLoad.SUCCESS,
            service_name="test_service"
        )

        imodels.BatchPatientLoad.objects.create(
            started=other_batch_start,
            stopped=other_batch_stop,
            state=imodels.InitialPatientLoad.SUCCESS,
            service_name="other_service"
        )
        self.assertEqual(
            load_utils.get_batch_start_time("test_service"),
            batch_start
        )


class AnyLoadsRunningTestCase(OpalTestCase):
    def setUp(self):
        super(AnyLoadsRunningTestCase, self).setUp()
        self.patient, _ = self.new_patient_and_episode_please()

    def test_any_loads_running_initial_patient_load(self):
        imodels.InitialPatientLoad.objects.create(
            state=imodels.InitialPatientLoad.RUNNING,
            patient=self.patient,
            started=timezone.now()
        )
        self.assertTrue(load_utils.any_loads_running())

    def test_any_loads_running_batch_patient_load(self):
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now()
        )
        self.assertTrue(load_utils.any_loads_running())

    def test_any_loads_running_none(self):
        self.assertFalse(load_utils.any_loads_running())

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
        self.assertFalse(load_utils.any_loads_running())


class GoodToGoTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        self.patient, _ = self.new_patient_and_episode_please()
        super(GoodToGoTestCase, self).setUp(*args, **kwargs)

    def test_no_initial_batch_load(self):
        self.assertTrue(load_utils.good_to_go("test_service"))

    @mock.patch.object(load_utils.logger, 'info')
    def test_last_load_running(self, info):
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now(),
            stopped=timezone.now(),
            service_name="test_service"
        )
        self.assertFalse(
            load_utils.good_to_go("test_service")
        )
        info.assert_called_once_with(
            "batch still running after 0 seconds, skipping"
        )

    @mock.patch.object(load_utils.logger, 'error')
    def test_last_load_still_running(self, error):
        diff = load_utils.MAX_ALLOWABLE_BATCH_RUN_TIME
        delta = datetime.timedelta(seconds=diff+1)
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.RUNNING,
            started=timezone.now() - delta,
            service_name="test_service"
        )
        self.assertFalse(load_utils.good_to_go("test_service"))
        error.assert_called_once_with(
            "Previous batch load for test_service still running after 3600 seconds"
        )


@mock.patch("intrahospital_api.services.base.load_utils.logger")
@mock.patch("intrahospital_api.services.base.load_utils.good_to_go")
class BatchLoadTestCase(OpalTestCase):
    def test_not_good_to_go(self, good_to_go, logger):
        good_to_go.return_value = False
        _batch_load = mock.MagicMock()
        _batch_load.__name__ = '_batch_load'
        batch_load = load_utils.batch_load(
            service_name="test_service"
        )(
            _batch_load
        )
        batch_load()
        good_to_go.return_value = False
        load_utils.batch_load("test_service")
        self.assertTrue(good_to_go.called)
        self.assertFalse(_batch_load.called)
        self.assertFalse(imodels.BatchPatientLoad.objects.exists())

    def test_good_to_go(self, good_to_go, logger):
        good_to_go.return_value = True
        _batch_load = mock.MagicMock(return_value=2)
        _batch_load.__name__ = '_batch_load'
        batch_load = load_utils.batch_load(
            service_name="test_service"
        )(
            _batch_load
        )
        batch_load()
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.count, 2)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.SUCCESS)
        self.assertTrue(good_to_go.called)
        self.assertTrue(_batch_load.called)

    def test_with_error(self, good_to_go, logger):
        good_to_go.return_value = True
        _batch_load = mock.MagicMock()
        _batch_load.side_effect = ValueError("Boom")
        _batch_load.__name__ = '_batch_load'
        batch_load = load_utils.batch_load(
            service_name="test_service"
        )(
            _batch_load
        )
        batch_load()
        bpl = imodels.BatchPatientLoad.objects.first()
        self.assertIsNotNone(bpl.started)
        self.assertIsNotNone(bpl.stopped)
        self.assertEqual(bpl.state, imodels.BatchPatientLoad.FAILURE)
        self.assertTrue(good_to_go.called)
        self.assertTrue(_batch_load.called)
        logger.error.assert_called_once_with("test_service batch load error")

