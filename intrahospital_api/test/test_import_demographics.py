import mock
import datetime
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands.import_demographics import Command
from intrahospital_api import models as imodels


@mock.patch(
    'intrahospital_api.management.commands.import_demographics.get_api'
)
class ImportDemographicsTestCase(OpalTestCase):
    def setUp(self):
        User.objects.create(username="ohc", password="fake_password")

    def test_handle_patient_found(self, get_api):
        get_api().demographics.return_value = dict(
            external_system="Test",
            date_of_birth=None,
            hospital_number="100",
            nhs_number="234",
            surname="Flintstone",
            first_name="Wilma",
            middle_name="somewhere",
            title="Ms",
            sex="Female",
            ethnicity="White Irish"
        )

        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="100"
        )
        Command().handle()
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
        get_api().demographics.assert_called_once_with("100")

    def test_handle_patient_not_found(self, get_api):
        get_api().demographics.return_value = None
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="100"
        )
        Command().handle()
        external_demographics = imodels.ExternalDemographics.objects.get()
        self.assertEqual(external_demographics.first_name, '')

    def test_handle_date_of_birth(self, get_api):
        get_api().demographics.return_value = dict(
            external_system="Test",
            date_of_birth=datetime.date(2000, 10, 27),
        )
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="100"
        )
        Command().handle()
        external_demographics = imodels.ExternalDemographics.objects.get()
        self.assertEqual(
            external_demographics.date_of_birth,
            datetime.date(2000, 10, 27)
        )

    def test_ignore_external_system_patients(self, get_api):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="100",
            external_system="job done"
        )
        Command().handle()
        self.assertFalse(get_api().demographics.called)
