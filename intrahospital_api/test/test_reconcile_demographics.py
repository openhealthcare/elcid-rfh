import mock
import datetime
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands.reconcile_demographics import Command
from intrahospital_api import models as imodels


class ReconcileDemographicsTestCase(OpalTestCase):
    def test_update_demographics(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.externaldemographics_set.update(
            hospital_number="100",
            first_name="Wilma",
            surname="Flintstone",
            date_of_birth=datetime.date(2000, 10, 1),
            title_ft="Ms",
            ethnicity_ft="White, Bedrock",
            nhs_number="123",
            middle_name="Bang Bang",
            sex_ft="Female"
        )
        patient.demographics_set.update(
            hospital_number="100",
            first_name="Wilma",
            surname="Flintstone",
            date_of_birth=datetime.date(2000, 10, 1)
        )
        cmd = Command()
        cmd.update_demographics(patient.externaldemographics_set.first())
        demographics = patient.demographics_set.first()
        self.assertEqual(
            demographics.external_system,
            "RFH Database"
        )

        self.assertEqual(demographics.sex, "Female")
        self.assertEqual(demographics.title, "Ms")
        self.assertEqual(demographics.ethnicity, "White, Bedrock")
        self.assertEqual(demographics.nhs_number, "123")
        self.assertEqual(demographics.middle_name, "Bang Bang")

    def test_handle(self):
        cmd = Command()
        patient, _ = self.new_patient_and_episode_please()

        with mock.patch.object(cmd, "update_demographics") as ud:
            cmd.handle()

        ud.assert_called_once_with(patient.externaldemographics_set.first())
