import json
# from django.test import override_settings
from mock import MagicMock, patch
from opal.core.test import OpalTestCase
# from opal.models import Patient
# from elcid.models import Allergies, Demographics
#
#
from elcid.api import GlossEndpointApi


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
class TestRefreshPatientApi(OpalTestCase):
    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

    def test_retrieve(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()
        patient_query.return_value = patient
        response = self.client.get("/elicdapi/v0.1/refresh_patient/1/")
        self.assertEqual(response.status_code, 200)
        serialised_patient = json.loads(response.content)
        self.assertEqual(serialised_patient["id"], patient.id)

    def test_retrieve_not_found_in_gloss(self, patient_query):
        patient, _ = self.new_patient_and_episode_please()
        patient_query.return_value = None

        response = self.client.get("/elicdapi/v0.1/refresh_patient/1/")
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
        response = self.client.get("/elicdapi/v0.1/refresh_patient/1/")
        self.assertEqual(response.status_code, 200)
        serialised_patient = json.loads(response.content)
        self.assertEqual(
            serialised_patient["demographics"][0]["first_name"],
            "Indiana"
        )
