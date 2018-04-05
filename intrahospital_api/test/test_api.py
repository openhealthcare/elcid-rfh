import mock
from rest_framework.reverse import reverse

from opal.core.test import OpalTestCase
from elcid import models as emodels
from intrahospital_api import api


class PatientToDict(OpalTestCase):
    def test_patient_to_dict(self):
        """ patient_to_dict should be logically equivellent of
            patient.to_dict() apart from lab tests
        """
        patient, episode = self.new_patient_and_episode_please()
        episode.set_tag_names(["something"], self.user)
        emodels.UpstreamLabTest.objects.create(
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
        self.assertEqual(
            to_dicted, result
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
