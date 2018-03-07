import mock
import datetime
from django.contrib.auth.models import User
from django.test import override_settings
from opal.core.test import OpalTestCase
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
            patient=patient
        )
        previous_load = imodels.BatchPatientLoad.objects.create()
        loader.initial_load()
        self.assertNotEqual(
            previous_load.id, imodels.BatchPatientLoad.objects.first().id
        )

        self.assertFalse(
            imodels.InitialPatientLoad.objects.exists()
        )
