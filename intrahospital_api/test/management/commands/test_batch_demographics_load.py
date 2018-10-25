from django.test import override_settings
from django.contrib.auth.models import User
from intrahospital_api.test.test_loader import ApiTestCase
from opal.models import Patient
from intrahospital_api.management.commands import batch_demographics_load
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api import models


class BatchDemographicsLoadTestCase(ApiTestCase):
    def setUp(self):
        super(BatchDemographicsLoadTestCase, self).setUp()
        self.handle = batch_demographics_load.Command().handle

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
            models.BatchPatientLoad.objects.filter(service_name="demographics").last().count,
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
            models.BatchPatientLoad.objects.filter(service_name="demographics").last().count,
            0
        )



