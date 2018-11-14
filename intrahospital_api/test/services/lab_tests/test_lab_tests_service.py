import mock
import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from opal import models as opal_models
from lab import models as lab_models
from elcid import models as elcid_models
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

    @mock.patch("intrahospital_api.services.lab_tests.service.service_utils")
    @mock.patch("intrahospital_api.services.lab_tests.service.update_patient")
    def test_multiple_patients(
        self, update_patient, service_utils
    ):
        api = service_utils.get_api.return_value
        api.lab_test_results_since.return_value = {
            "111": ["some_lab_tests"],
            "112": ["some_other_lab_tests"],
        }
        patient_1, _ = self.new_patient_and_episode_please()
        patient_2, _ = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            hospital_number="111", first_name="Wilma", surname="Flintstone"
        )
        patient_2.demographics_set.update(
            hospital_number="112", first_name="Betty", surname="Rubble"
        )
        service.update_patients(
            opal_models.Patient.objects.filter(
                id__in=[patient_1.id, patient_2.id]
            ),
            datetime.datetime.now()
        )

        call_args_list = update_patient.call_args_list
        self.assertEqual(
            call_args_list[0], mock.call(patient_1, ['some_lab_tests'])
        )
        self.assertEqual(
            call_args_list[1], mock.call(patient_2, ['some_other_lab_tests'])
        )


class GetModelForLabTestTypeTestCase(OpalTestCase):
    def setUp(self):
        super(GetModelForLabTestTypeTestCase, self).setUp()
        self.patient, _ = self.new_patient_and_episode_please()

    def get_lab_test_dict(self, **kwargs):
        lab_test = dict(
            test_name="BLOOD CULTURE",
            external_identifier="1",
        )
        lab_test.update(kwargs)
        return lab_test

    def create_lab_test(self, lab_test_updates, extras_updates):
        if lab_test_updates is None:
            lab_test_updates = {}

        if extras_updates is None:
            extras_updates = {}

        lab_test = lab_models.LabTest.objects.create(
            patient=self.patient, **lab_test_updates
        )
        lab_test.extras = extras_updates
        lab_test.save()
        return lab_test

    def test_blood_culture_found(self):
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamBloodCulture.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="BLOOD CULTURE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict()
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertEqual(
            lab_test.id, result.id
        )

    def test_upstream_lab_test_found(self):
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="LIVER PROFILE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict(
            test_name="LIVER PROFILE"
        )
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertEqual(
            lab_test.id, result.id
        )

    def test_upstream_blood_culture_not_found(self):
        lab_test_dict = self.get_lab_test_dict()
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamBloodCulture
        )

    def test_upstream_lab_test_not_found(self):
        lab_test_dict = self.get_lab_test_dict(test_name="LIVER PROFILE")
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamLabTest
        )

    def test_does_not_return_wrong_model_type_blood_culture(self):
        """
        If we are looking for an Upstream Blood Culture
        with id "1" we should not return an
        Upstream Lab Test
        """
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamBloodCulture.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="BLOOD CULTURE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict(test_name="LIVER PROFILE")
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamLabTest
        )

    def test_does_not_return_wrong_model_type_lab_test(self):
        """
        If we are looking for an Upstream Blood Culture
        with id "1" we should not return an
        Upstream Lab Test
        """
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="LIVER PROFILE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict(test_name="BLOOD CULTURE")
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamBloodCulture
        )

    def test_multiple_tests(self):
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="LIVER PROFILE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )

        lab_test_dict = self.get_lab_test_dict(
            test_name="LIVER PROFILE"
        )
        with self.assertRaises(ValueError) as ve:
            service.get_model_for_lab_test_type(
                self.patient, lab_test_dict
            )
        self.assertEqual(
            str(ve.exception), "multiple test types found for 1 LIVER PROFILE"
        )

