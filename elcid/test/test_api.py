import json
import copy
import datetime
from django.test import override_settings
from django.utils import timezone
from mock import MagicMock, patch
from opal.core.test import OpalTestCase
from rest_framework.reverse import reverse
from elcid import api
from lab import models as lmodels
from opal import models as omodels


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
            dict(observation_value="1"),
            dict(observation_value="3"),
            dict(observation_value="2"),
        ]
        self.assertEqual(
            api.generate_time_series(observations),
            [1, 3, 2]
        )

    def test_get_observation_value(self):
        to_obs = lambda x: {"observation_value": x}
        self.assertEqual(api.get_observation_value(to_obs("0.1~")), 0.1)
        self.assertIsNone(api.get_observation_value(to_obs("as")))

    def test_clean_ref_range(self):
        self.assertEqual(api.clean_ref_range(" [ 1 - 2 ] "), "1 - 2")

    def test_get_reference_range(self):
        to_obs = lambda x: {"reference_range": x}
        self.assertIsNone(api.get_reference_range(to_obs(" - ")))
        self.assertIsNone(api.get_reference_range(to_obs("1 - 2 - 3")))
        self.assertEqual(
            api.get_reference_range(to_obs("[1 - 2]")),
            {"min": "1", "max": "2"}
        )


class LabTestSummaryApiTestCase(OpalTestCase):
    def setUp(self):
        self.request = self.rf.get("/")
        self.now = timezone.make_aware(
            datetime.datetime.now(),
            timezone.get_current_timezone()
        )
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(hospital_number="123")
        url = reverse(
            "lab_test_summary_api-detail",
            kwargs=dict(pk=self.patient.id),
            request=self.request
        )
        unneeded_lab_test_extras = dict(
            profile_description="UNEEDED",
            observations=[
                dict(
                    observation_value="11~5",
                    reference_range="10 - 12.2",
                    units='s',
                    test_name='Alkaline Phosphatase'
                ),
            ]
        )

        # we should not pull out this test, even though
        # one of the observation names is the same
        # as one that we want.
        self.uneeded_lab_test = lmodels.LabTest.objects.create(
            patient=self.patient,
            datetime_ordered=self.now,
            lab_test_type='HL7 Result',
            extras=unneeded_lab_test_extras
        )

        full_blood_count_extras = dict(
            profile_description="FULL BLOOD COUNT",
            observations=[
                dict(
                    observation_value="11~5",
                    reference_range="12 - 12.2",
                    units='s',
                    test_name='WBC'
                ),
                dict(
                    observation_value="11~5",
                    reference_range="11 - 12.2",
                    units='s',
                    test_name='Lymphocytes'
                ),
                dict(
                    observation_value="11~5",
                    reference_range="10 - 12.2",
                    units='s',
                    test_name='Not included'
                ),
            ]
        )

        self.previous_date = self.now - datetime.timedelta(1)
        self.full_blood_count = lmodels.LabTest.objects.create(
            patient=self.patient,
            datetime_ordered=self.previous_date,
            lab_test_type='HL7 Result',
            extras=full_blood_count_extras
        )

        full_blood_count_extras_2 = copy.copy(full_blood_count_extras)
        full_blood_count_extras_2["observations"][0]["observation_value"] = "12"
        self.full_blood_count_2 = lmodels.LabTest.objects.create(
            patient=self.patient,
            datetime_ordered=self.now,
            lab_test_type='HL7 Result',
            extras=full_blood_count_extras_2
        )

        liver_profile_extras = dict(
            profile_description="LIVER PROFILE",
            observations=[
                dict(
                    observation_value="11~5",
                    reference_range="10 - 12.2",
                    units='s',
                    test_name='Alkaline Phosphatase'
                ),
            ]
        )

        self.liver_profile = lmodels.LabTest.objects.create(
            patient=self.patient,
            datetime_ordered=self.now,
            lab_test_type='HL7 Result',
            extras=liver_profile_extras
        )
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

        self.result = self.client.get(url).data

    def test_sort_observations_in_preferred_order(self):
        """
            should order in distinct order
        """
        self.assertEqual(
            [i["name"] for i in self.result["obs_values"]],
            [u'WBC', u'Lymphocytes', u'Alkaline Phosphatase']
        )

    def test_aggregate_observations(self):
        aggregated = api.LabTestSummaryApi().aggregate_observations(
            self.patient
        )
        self.assertNotIn('UNEEDED', aggregated)
        self.assertIn('Alkaline Phosphatase', aggregated["LIVER PROFILE"])

        self.assertIn("WBC", aggregated["FULL BLOOD COUNT"])
        self.assertEqual(len(aggregated["FULL BLOOD COUNT"]["WBC"]), 2)
        WBC = aggregated["FULL BLOOD COUNT"]["WBC"]
        self.assertEqual(WBC[0]["datetime_ordered"], self.previous_date)
        self.assertEqual(WBC[0]["observation_value"], "11~5")

        self.assertEqual(WBC[1]["datetime_ordered"], self.now)
        self.assertEqual(WBC[1]["observation_value"], "12")

    def test_retrieve_recent_dates(self):
        self.assertEqual(
            self.result["recent_dates"],
            [self.previous_date, self.now]
        )

    @override_settings(GLOSS_ENABLED=True)
    @patch('elcid.api.gloss_api.patient_query')
    def test_gloss_settings_are_used(self, patient_query):
        api.LabTestSummaryApi().retrieve(self.request, 1)
        patient_query.assert_called_once_with('123')


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
        self.assertEqual(omodels.PatientRecordAccess.objects.count(), 0)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(patient_query.called)
        self.assertEqual(omodels.PatientRecordAccess.objects.count(), 1)
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
