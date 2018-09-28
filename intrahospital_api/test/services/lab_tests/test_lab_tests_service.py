import mock
import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from opal import models as opal_models
from intrahospital_api.services.lab_tests import service
from intrahospital_api import models
from intrahospital_api.test import test_loader


@mock.patch('intrahospital_api.services.lab_tests.service.update_patients')
class BatchLoadTestCase(test_loader.ApiTestCase):
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
        result = service.lab_test_batch_load()
        call_args = update_patients.call_args
        self.assertEqual(
            call_args[0][0].get(), patient
        )

        self.assertEqual(
            call_args[0][1], started
        )

        self.assertEqual(result, 2)


class UpdatePatientsTestCase(test_loader.ApiTestCase):

    @mock.patch("intrahospital_api.services.lab_tests.service.update_patient")
    def test_multiple_patients_with_the_same_hospital_number(
        self, update_patient
    ):
        patient_1, _ = self.new_patient_and_episode_please()
        patient_2, _ = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            hospital_number="111", first_name="Wilma", surname="Flintstone"
        )
        patient_2.demographics_set.update(
            hospital_number="111", first_name="Betty", surname="Rubble"
        )
        service.update_patients(
            opal_models.Patient.objects.filter(
                id__in=[patient_1.id, patient_2.id]
            ),
            datetime.datetime.now()
        )

        call_args_list = update_patient.call_args_list
        called_patients = set([
            call_args_list[0][0][0],
            call_args_list[1][0][0]
        ])

        self.assertEqual(
            called_patients, set([patient_1, patient_2])
        )


