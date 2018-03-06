import mock
import datetime
from django.contrib.auth.models import User
from django.test import override_settings
from opal.core.test import OpalTestCase
from intrahospital_api import models as imodels
from intrahospital_api import loader
from intrahospital_api.constants import EXTERNAL_SYSTEM


@override_settings(API_USER="ohc")
class ImportDemographicsTestCase(OpalTestCase):
    def setUp(self):
        User.objects.create(username="ohc", password="fake_password")

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
