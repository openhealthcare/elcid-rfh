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


@override_settings(API_USER="ohc")
class LoaderTestCase(OpalTestCase):
    def setUp(self):
        super(LoaderTestCase, self).setUp()
        User.objects.create(username="ohc", password="fake_password")


class ImportDemographicsTestCase(LoaderTestCase):
    def test_handle_patient_found(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="100"
        )
        with mock.patch.object(loader.api, "demographics") as d:
            d.return_value = dict(
                date_of_birth=None,
                hospital_number="100",
                nhs_number="234",
                surname="Flintstone",
                first_name="Wilma",
                middle_name="somewhere",
                title="Ms",
                sex="Female",
                ethnicity="White Irish",
                external_system=EXTERNAL_SYSTEM,
            )
            loader.reconcile_demographics()
        external_demographics = imodels.ExternalDemographics.objects.get()
        self.assertEqual(external_demographics.date_of_birth, None)
        self.assertEqual(external_demographics.hospital_number, "100")
        self.assertEqual(external_demographics.nhs_number, "234")
        self.assertEqual(external_demographics.surname, "Flintstone")
        self.assertEqual(external_demographics.first_name, "Wilma")
        self.assertEqual(external_demographics.middle_name, "somewhere")
        self.assertEqual(external_demographics.title, "Ms")
        self.assertEqual(external_demographics.sex, "Female")
        self.assertEqual(external_demographics.ethnicity, "White Irish")
        d.assert_called_once_with("100")

    def test_handle_patient_not_found(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="100",
            external_system=EXTERNAL_SYSTEM,
        )
        with mock.patch.object(loader.api, "demographics") as d:
            d.return_value = None
            loader.reconcile_demographics()

        external_demographics = imodels.ExternalDemographics.objects.get()
        self.assertEqual(external_demographics.first_name, '')

    def test_handle_date_of_birth(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            external_system="test",
        )
        with mock.patch.object(loader.api, "demographics") as d:
            d.return_value = dict(
                external_system="Test",
                date_of_birth="27/10/2000",
                first_name="Jane",
                surname="Doe",
                hospital_number="123"
            )
            loader.reconcile_demographics()
        external_demographics = imodels.ExternalDemographics.objects.get()
        self.assertEqual(
            external_demographics.date_of_birth,
            datetime.date(2000, 10, 27)
        )

    def test_ignore_external_system_patients(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="100",
            external_system=EXTERNAL_SYSTEM
        )
        with mock.patch.object(loader.api, "demographics") as d:
            loader.reconcile_demographics()

        self.assertFalse(d.called)


class HaveDemographicsTestCase(LoaderTestCase):
    def setUp(self, *args, **kwargs):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="James",
            surname="Watson",
            sex_ft="Male",
            religion="Christian"
        )
        self.demographics = patient.demographics_set.first()
        super(HaveDemographicsTestCase, self).setUp(*args, **kwargs)

    def test_demographics_have_not_changed(self):
        update_dict = dict(
            first_name="James",
            surname="Watson",
            sex="Male"
        )
        self.assertFalse(
            loader.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_need_to_update_demographics_fk_or_ft(self):
        update_dict = dict(
            first_name="James",
            surname="Watson",
            sex="not disclosed"
        )
        self.assertTrue(
            loader.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_need_to_update_demographics_str(self):
        update_dict = dict(
            first_name="Jamey",
            surname="Watson",
            sex="Male"
        )

        self.assertTrue(
            loader.have_demographics_changed(
                update_dict, self.demographics
            )
        )


@mock.patch("intrahospital_api.loader._initial_load")
@mock.patch("intrahospital_api.loader.log_errors")
class InitialLoadTestCase(LoaderTestCase):
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


class _InitialLoadTestCase(LoaderTestCase):
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
        "intrahospital_api.loader.reconcile_demographics",
    )
    @mock.patch(
        "intrahospital_api.loader.load_patient",
    )
    def test_flow(self, load_patient, reconcile_demographics):
        with mock.patch.object(loader.logger, "info") as info:
            loader._initial_load()
            reconcile_demographics.assert_called_once_with()
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
    def test_intergration(self):
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

            upstream_patients = emodels.UpstreamLabTest.objects.values_list(
                "patient_id", flat=True
            ).distinct()
            self.assertEqual(
                set([self.patient_1.id, self.patient_2.id]),
                set(upstream_patients)
            )


class LogErrorsTestCase(LoaderTestCase):
    @mock.patch(
        "intrahospital_api.loader.logging.getLogger",
    )
    @mock.patch.object(loader.logger, "error")
    def test_log_errors(self, err, getLogger):
        loader.log_errors("blah")
        getLogger.assert_called_once_with("error_emailer")
        getLogger().error.assert_called_once_with(
            "unable to run blah"
        )
        self.assertTrue(err.called)


class AnyLoadsRunningTestCase(LoaderTestCase):
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


class LoadDemographicsTestCase(LoaderTestCase):

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
    def test_intergration(self):
        result = loader.load_demographics("some_number")
        self.assertTrue(isinstance(result, dict))


@mock.patch('intrahospital_api.loader.async_task')
@mock.patch('intrahospital_api.loader._load_patient')
class LoadLabTestsForPatientTestCase(LoaderTestCase):
    def setUp(self, *args, **kwargs):
        super(LoadLabTestsForPatientTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()

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
class AsyncTaskTestCase(LoaderTestCase):
    def test_async_task(self, delay):
        patient, _ = self.new_patient_and_episode_please()
        patient_load = imodels.InitialPatientLoad.objects.create(
            patient=patient,
            started=timezone.now()
        )
        loader.async_task(patient, patient_load)
        delay.assert_called_once_with(patient, patient_load)


class GoodToGoTestCase(LoaderTestCase):
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
class BatchLoadTestCase(LoaderTestCase):
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


@mock.patch.object(loader.logger, 'info')
@mock.patch.object(loader.api, 'demographics')
class ReconcileDemographicsTestCase(LoaderTestCase):
    def setUp(self, *args, **kwargs):
        super(ReconcileDemographicsTestCase, self).setUp(*args, **kwargs)

        # this is the patient that will be covered
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            external_system="blah",
            hospital_number="123",
            updated=None
        )
        # we should not see this patient as they have an exernal system on
        # their demographics
        patient_2, _ = self.new_patient_and_episode_please()
        patient_2.demographics_set.update(
            external_system=EXTERNAL_SYSTEM,
            hospital_number="234",
        )

    def test_reconcile_demographics(self, demographics, info):
        demographics.return_value = dict(
            first_name="Jane",
            surname="Doe",
            date_of_birth="12/10/2000",
            external_system=EXTERNAL_SYSTEM,
            hospital_number="123"
        )
        loader.reconcile_demographics()
        demographics.assert_called_once_with("123")
        self.assertFalse(info.called)
        self.assertEqual(
            self.patient.externaldemographics_set.first().first_name,
            "Jane"
        )
        self.assertIsNotNone(
            self.patient.externaldemographics_set.first().updated
        )

    def test_with_external_demographics_when_none(self, demographics, info):
        demographics.return_value = None
        loader.reconcile_demographics()
        self.assertIsNone(
            self.patient.externaldemographics_set.first().updated
        )
        info.assert_called_once_with("unable to find 123")


@mock.patch.object(loader.api, "data_deltas")
@mock.patch('intrahospital_api.loader.reconcile_demographics')
@mock.patch('intrahospital_api.loader.update_from_batch')
class _BatchLoadTestCase(OpalTestCase):
    def test_batch_load(
        self, update_from_batch, reconcile_demographics, data_deltas
    ):
        now = timezone.now()
        imodels.BatchPatientLoad.objects.create(
            state=imodels.BatchPatientLoad.SUCCESS,
            started=now
        )
        data_deltas.return_value = "something"
        loader._batch_load()
        reconcile_demographics.assert_called_once_with()
        data_deltas.assert_called_once_with(now)
        update_from_batch.assert_called_once_with("something")


class UpdateFromBatchTestCase(OpalTestCase):
    def test_update_from_batch(self):
        pass
