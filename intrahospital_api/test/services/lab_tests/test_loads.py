import mock
import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api.services.lab_tests import loads
from intrahospital_api import models


@mock.patch('intrahospital_api.lab_tests.loads.service.update_patients')
class BatchLoadTestCase(OpalTestCase):
    def test_batch_load(self, update_patients):
        patient, _ = self.new_patient_and_episode_please()
        started = timezone.now() - datetime.timedelta(seconds=20)
        stopped = timezone.now() - datetime.timedelta(seconds=10)
        models.InitialPatientLoad.objects.create(
            started=started,
            stopped=stopped,
            patient=patient,
            state=models.InitialPatientLoad.SUCCESS
        )
        update_patients.return_value = 2
        result = loads.lab_test_batch_load()
        call_args = update_patients.call_args
        self.assertEqual(
            call_args[0][0].get(), patient
        )

        self.assertEqual(
            call_args[0][1], started
        )

        self.assertEqual(result, 2)


