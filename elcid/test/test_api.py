import json
from mock import MagicMock, patch
from opal.core.test import OpalTestCase
from rest_framework.reverse import reverse
from elcid.api import GlossEndpointApi
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
        endpoint = GlossEndpointApi()
        endpoint.create(request)
        bulk_create.assert_called_once_with(expected_dict)


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

    def test_retrieve(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()
        patient_query.return_value = patient
        self.assertEqual(models.PatientRecordAccess.objects.count(), 0)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.PatientRecordAccess.objects.count(), 1)
        serialised_patient = json.loads(response.content)
        self.assertEqual(serialised_patient["id"], patient.id)

    def test_retrieve_not_found_in_gloss(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()
        patient_query.return_value = None
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        serialised_patient = json.loads(response.content)
        self.assertEqual(serialised_patient["id"], patient.id)

    def test_retrieve_updates_patient_from_gloss(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()

        def update_patient(hospital_number):
            demographics = patient.demographics_set.first()
            demographics.first_name = "Indiana"
            demographics.save()

        patient_query.side_effect = update_patient
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        serialised_patient = json.loads(response.content)
        self.assertEqual(
            serialised_patient["demographics"][0]["first_name"],
            "Indiana"
        )
