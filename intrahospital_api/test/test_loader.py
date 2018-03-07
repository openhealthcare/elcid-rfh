import mock
import datetime
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from opal.core.test import OpalTestCase
from elcid import models as emodels
from intrahospital_api import models as imodels
from intrahospital_api import loader
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
            loader.update_external_demographics()
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
            loader.update_external_demographics()

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
                date_of_birth="27/10/2000"
            )
            loader.update_external_demographics()
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
            loader.update_external_demographics()

        loader.update_external_demographics()
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
        "intrahospital_api.loader.update_external_demographics",
    )
    @mock.patch(
        "intrahospital_api.loader.load_lab_tests_for_patient",
    )
    def test_flow(self, load_lab_tests_for_patient, external_demographics):
        with mock.patch.object(loader.logger, "info") as info:
            loader._initial_load()
            external_demographics.assert_called_once_with()
            call_args_list = load_lab_tests_for_patient.call_args_list
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
