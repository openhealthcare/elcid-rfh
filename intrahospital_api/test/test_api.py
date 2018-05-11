import mock
from rest_framework.reverse import reverse

from opal.core.test import OpalTestCase
from elcid import models as emodels
from intrahospital_api import api
from intrahospital_api import constants


class PatientToDict(OpalTestCase):
    def test_patient_to_dict(self):
        """ patient_to_dict should be logically equivellent of
            patient.to_dict() apart from lab tests.

            Lab tests should exclude anything whith an external
            system, which in practical terms means UpstreamLabTests
            and UpstreamBloodCultures at present.
        """
        patient, episode = self.new_patient_and_episode_please()
        episode.set_tag_names(["something"], self.user)
        emodels.UpstreamLabTest.objects.create(
            patient=patient,
            external_system=constants.EXTERNAL_SYSTEM

        )
        emodels.QuickFISH.objects.create(
            patient=patient
        )
        emodels.Imaging.objects.create(episode=episode, site="elbow")
        patient.demographics_set.update(
            first_name="Wilma",
            hospital_number="1"
        )
        to_dicted = patient.to_dict(self.user)
        to_dicted.pop("lab_test")
        to_dicted["episodes"][episode.id].pop("lab_test")
        to_dicted["episodes"][episode.id].pop("episode_history")
        result = api.patient_to_dict(patient, self.user)
        found_lab_tests_for_patient = result.pop("lab_test")
        found_lab_tests_for_episode = result["episodes"][episode.id].pop(
            "lab_test"
        )

        self.assertEqual(
            to_dicted, result
        )
        self.assertEqual(len(found_lab_tests_for_patient), 1)
        self.assertEqual(
            found_lab_tests_for_patient[0]["lab_test_type"],
            emodels.QuickFISH.get_display_name()
        )
        self.assertEqual(
            found_lab_tests_for_episode, found_lab_tests_for_patient
        )

    @mock.patch("intrahospital_api.api.patient_to_dict")
    def test_get(self, patient_to_dict):
        self.request = self.rf.get("/")
        patient, _ = self.new_patient_and_episode_please()

        patient_to_dict.return_value = {"some_data": "some_data"}
        url = reverse(
            'patient-detail',
            kwargs=dict(pk=patient.id),
            request=self.rf.get("/")
        )
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        result = self.client.get(url)
        self.assertEqual(
            result.data, {"some_data": "some_data"}
        )

    @mock.patch("intrahospital_api.api.patient_to_dict")
    def test_login_required(self, patient_to_dict):
        self.request = self.rf.get("/")
        patient, _ = self.new_patient_and_episode_please()

        patient_to_dict.return_value = {"some_data": "some_data"}
        url = reverse(
            'patient-detail',
            kwargs=dict(pk=patient.id),
            request=self.rf.get("/")
        )

        result = self.client.get(url)
        self.assertEqual(result.status_code, 401)
