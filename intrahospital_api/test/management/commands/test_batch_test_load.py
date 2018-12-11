from django.test import override_settings
from intrahospital_api.management.commands import batch_test_load
from intrahospital_api import constants
from intrahospital_api.models import InitialPatientLoad, BatchPatientLoad
from intrahospital_api.test.core import ApiTestCase


class BatchLoadTestCase(ApiTestCase):
    def setUp(self):
        super(BatchLoadTestCase, self).setUp()
        self.handle = batch_test_load.Command().handle

    def test_integration(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Wilma",
            hospital_number="111",
        )
        i = InitialPatientLoad(patient=patient)
        i.start()
        i.complete()

        self.assertFalse(patient.labtest_set.exists())
        self.handle()
        self.assertTrue(patient.labtest_set.exists())
        last_batch_load = BatchPatientLoad.objects.filter(
            service_name="lab_tests"
        ).last()
        self.assertEqual(
            last_batch_load.count,
            patient.labtest_set.count()
        )


