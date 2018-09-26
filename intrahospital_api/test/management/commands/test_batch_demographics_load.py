from django.test import override_settings
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from opal.models import Patient
from intrahospital_api.management.commands import batch_demographics_load
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api import models


@override_settings(API_USER="api_user")
class BatchDemographicsLoadTestCase(OpalTestCase):
    def setUp(self):
        self.handle = batch_demographics_load.Command().handle
        user = User.objects.create(username="api_user")
        user.set_password("password")
        user.save()

    def test_intergration_external(self):
        patient_1, _ = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone",
            external_system=EXTERNAL_SYSTEM
        )
        self.handle()
        demographics = patient_1.demographics_set.first()

        self.assertNotEqual(
            demographics.first_name, "Wilma"
        )
        self.assertNotEqual(
            demographics.surname, "Flintstone"
        )
        self.assertTrue(
            bool(demographics.date_of_birth)
        )

        self.assertEqual(
            models.BatchPatientLoad.objects.first().count,
            1
        )

    def test_intergration_not_external(self):
        """
        A patient that does not have external demographics
        and does not match with anything will
        not be reconciled
        """
        patient_1, _ = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone"
        )
        self.handle()
        demographics = patient_1.demographics_set.first()

        self.assertEqual(
            demographics.first_name, "Wilma"
        )
        self.assertEqual(
            demographics.surname, "Flintstone"
        )
        self.assertFalse(
            bool(demographics.date_of_birth)
        )

        self.assertEqual(
            models.BatchPatientLoad.objects.first().count,
            0
        )



