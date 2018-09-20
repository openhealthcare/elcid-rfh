import mock
from rest_framework.reverse import reverse

from opal.core.test import OpalTestCase
from opal import models as omodels
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
        self.maxDiff = None
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

    def test_contains_empty_episode_subrecords(self):
        """
        We populate empty subrecords with an empty list
        """
        patient, episode = self.new_patient_and_episode_please()
        result = api.patient_to_dict(patient, self.user)
        self.assertEqual(
            result["episodes"][episode.id]["antimicrobial"], []
        )

    def test_contains_empty_patient_subrecords(self):
        """
        We populate empty subrecords with an empty list
        """
        patient, episode = self.new_patient_and_episode_please()
        result = api.patient_to_dict(patient, self.user)
        self.assertEqual(
            result["house_owner"], []
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


@mock.patch("intrahospital_api.api.lab_test_service.lab_tests_for_hospital_number")
class UpstreamDataViewsetTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.url = reverse(
            'upstream-detail',
            kwargs=dict(pk=self.patient.id),
            request=self.rf.get("/")
        )

    def get_response(self, patient_id=None):
        if patient_id is None:
            patient_id = self.patient.id
        url = reverse(
            'upstream-detail',
            kwargs=dict(pk=patient_id),
            request=self.rf.get("/")
        )
        return self.client.get(url)

    def test_get_found(self, lab_tests_for_hospital_number):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        result = dict(some="results")
        lab_tests_for_hospital_number.return_value = result
        response = self.get_response()
        self.assertEqual(
            response.data, result
        )

    def test_get_not_found(self, lab_tests_for_hospital_number):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        result = dict(some="results")
        lab_tests_for_hospital_number.return_value = result
        other_patient_id = omodels.Patient.objects.order_by("id").last().id + 1
        self.assertEqual(self.get_response(other_patient_id).status_code, 404)

    def test_not_logged_in(self, lab_tests_for_hospital_number):
        result = dict(some="results")
        lab_tests_for_hospital_number.return_value = result
        self.assertEqual(self.get_response().status_code, 401)
