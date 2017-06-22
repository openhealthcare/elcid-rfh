import json
from django.test import override_settings
from mock import MagicMock, patch
from opal.core.test import OpalTestCase
from rest_framework.reverse import reverse
from elcid import api
from opal import models


class TestEndPoint(OpalTestCase):
    @patch("elcid.api.gloss_api.bulk_create_from_gloss_response")
    def test_create(self, bulk_create):
        request = MagicMock()
        expected_dict = dict(
            messages=[],
            hospital_number="1"
        )
        request.data = json.dumps(expected_dict)
        endpoint = api.GlossEndpointApi()
        endpoint.create(request)
        bulk_create.assert_called_once_with(expected_dict)


class ApiUtilsTestCase(OpalTestCase):
    def test_generate_time_series(self):
        observations = [
            dict(observation_value=1),
            dict(observation_value=3),
            dict(observation_value=2),
        ]
        self.assertEqual(
            api.generate_time_series(observations),
            [1, 3, 2]
        )

    def test_get_observation_value(self):
        pass

    def test_clean_ref_range(self):
        pass

    def test_get_reference_range(self):
        pass

class LabTestSummaryApiTestCase(OpalTestCase):
    def test_sort_observations_in_preferred_order(self):
        pass

    def test_sort_observations_not_in_preferred_order(self):
        pass

    def test_aggregate_observations(self):
        pass

    def test_aggregate_tests_we_dont_care_about(self):
        pass

    def test_aggregate_observations_we_dont_care_about(self):
        pass

    def test_retrieve_recent_dates(self):
        pass

    def test_retrieve_sorted(self):
        pass

    def test_retrieve_serialised_data(self):
        pass


@patch('elcid.api.gloss_api.patient_query')
class GlossApiQueryMonkeyPatchTestCase(OpalTestCase):
    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        request = self.rf.get("/")
        self.url = reverse(
            "patient-detail",
            kwargs=dict(pk=1),
            request=request
        )

    @override_settings(GLOSS_ENABLED=True)
    def test_retrieve(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()
        patient_query.return_value = patient
        self.assertEqual(models.PatientRecordAccess.objects.count(), 0)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(patient_query.called)
        self.assertEqual(models.PatientRecordAccess.objects.count(), 1)
        serialised_patient = json.loads(response.content)
        self.assertEqual(serialised_patient["id"], patient.id)

    @override_settings(GLOSS_ENABLED=True)
    def test_retrieve_not_found_in_gloss(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()
        patient_query.return_value = None
        response = self.client.get(self.url)
        self.assertTrue(patient_query.called)
        self.assertEqual(response.status_code, 200)
        serialised_patient = json.loads(response.content)
        self.assertEqual(serialised_patient["id"], patient.id)

    @override_settings(GLOSS_ENABLED=True)
    def test_retrieve_updates_patient_from_gloss(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()

        def update_patient(hospital_number):
            demographics = patient.demographics_set.first()
            demographics.first_name = "Indiana"
            demographics.save()

        patient_query.side_effect = update_patient
        response = self.client.get(self.url)
        self.assertTrue(patient_query.called)
        self.assertEqual(response.status_code, 200)
        serialised_patient = json.loads(response.content)
        self.assertEqual(
            serialised_patient["demographics"][0]["first_name"],
            "Indiana"
        )

    @override_settings(GLOSS_ENABLED=False)
    def test_dont_retrieve_if_gloss_is_disabled(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(first_name="Indiana")
        response = self.client.get(self.url)
        self.assertFalse(patient_query.called)
        self.assertEqual(response.status_code, 200)
        serialised_patient = json.loads(response.content)
        self.assertEqual(
            serialised_patient["demographics"][0]["first_name"],
            "Indiana"
        )
