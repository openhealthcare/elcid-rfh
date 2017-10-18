import json
import datetime
from django.test import override_settings
from mock import MagicMock, patch
from opal.core.test import OpalTestCase
from rest_framework.reverse import reverse
from elcid.api import GlossEndpointApi, BloodCultureResultApi
from opal import models
from elcid import models as emodels


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


class BloodCultureResultApiTestCase(OpalTestCase):
    def setUp(self):
        self.api = BloodCultureResultApi()

    def test_sort_by_date_ordered_and_lab_number_by_date(self):
        some_keys = [
            (datetime.date(2017, 10, 1), "123222",),
            (datetime.date(2017, 10, 2), "123222",),
        ]

        expected = [
            (datetime.date(2017, 10, 2), "123222",),
            (datetime.date(2017, 10, 1), "123222",),
        ]

        result = self.api.sort_by_date_ordered_and_lab_number(some_keys)
        self.assertEqual(
            result, expected
        )

    def test_sort_by_date_ordered_and_lab_number_by_lab_number(self):
        some_keys = [
            (datetime.date(2017, 10, 1), "123222",),
            (datetime.date(2017, 10, 1), "123228",),
        ]

        expected = [
            (datetime.date(2017, 10, 1), "123228",),
            (datetime.date(2017, 10, 1), "123222",),
        ]

        result = self.api.sort_by_date_ordered_and_lab_number(some_keys)
        self.assertEqual(
            result, expected
        )

    def test_sort_by_date_ordered_and_lab_number_primacy(self):
        some_keys = [
            (datetime.date(2017, 10, 2), "123222",),
            (datetime.date(2017, 10, 1), "123228",),
        ]

        expected = [
            (datetime.date(2017, 10, 2), "123222",),
            (datetime.date(2017, 10, 1), "123228",),
        ]

        result = self.api.sort_by_date_ordered_and_lab_number(some_keys)
        self.assertEqual(
            result, expected
        )

    def test_sort_by_date_ordered_and_lab_number_no_lab_number(self):
        some_keys = [
            (datetime.date(2017, 10, 1), "",),
            (datetime.date(2017, 10, 1), "123228",),
        ]

        expected = [
            (datetime.date(2017, 10, 1), "123228",),
            (datetime.date(2017, 10, 1), "",),
        ]

        result = self.api.sort_by_date_ordered_and_lab_number(some_keys)
        self.assertEqual(
            result, expected
        )

    def test_sort_by_date_ordered_and_lab_number_no_date_ordered(self):
        some_keys = [
            (None, "123228",),
            (datetime.date(2017, 10, 1), "123228",),
        ]

        expected = [
            (None, "123228",),
            (datetime.date(2017, 10, 1), "123228",),
        ]

        result = self.api.sort_by_date_ordered_and_lab_number(some_keys)
        self.assertEqual(
            result, expected
        )

    def test_sort_by_lab_test_order(self):
        lab_tests = [
            dict(lab_test_type="Organism"),
            dict(lab_test_type="GNR"),
            dict(lab_test_type="GPC Strep"),
            dict(lab_test_type="GPC Staph"),
            dict(lab_test_type="QuickFISH"),
            dict(lab_test_type="Gram Stain")
        ]

        expected = list(lab_tests)
        expected.reverse()
        result = self.api.sort_by_lab_test_order(lab_tests)
        self.assertEqual(
            result, expected
        )

    def test_translate_date_to_string(self):
        some_date = datetime.date(2017, 3, 1)
        self.assertEqual(
            self.api.translate_date_to_string(some_date),
            "01/03/2017"
        )

    def test_translate_date_to_string_none(self):
        some_date = ""
        self.assertEqual(
            self.api.translate_date_to_string(some_date), ""
        )

    def test_retrieve(self):
        request = self.rf.get("/")
        url = reverse(
            "blood_culture_results-detail",
            kwargs=dict(pk=1),
            request=request
        )
        some_date = datetime.date(2017, 1, 1)
        patient, _ = self.new_patient_and_episode_please()

        gram_stain = emodels.GramStain.objects.create(
            date_ordered=some_date,
            patient=patient,
        )

        gram_stain.extras = dict(
            lab_number="212",
            aerobic=False,
            isolate=1
        )
        gram_stain.save()
        gram_stain.result.result = "Yeast"
        gram_stain.result.lab_test_id = gram_stain.id
        gram_stain.result.save()

        some_other_date = datetime.date(2017, 1, 2)
        quick_fish = emodels.QuickFISH.objects.create(
            date_ordered=some_other_date,
            patient=patient,
        )

        quick_fish.extras = dict(
            lab_number="212",
            aerobic=True,
            isolate=2
        )
        quick_fish.save()
        quick_fish.result.result = "C. albicans"
        quick_fish.result.lab_test_id = quick_fish.id
        quick_fish.result.save()
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        contents = json.loads(result.content)

        found_culture_order = contents["culture_order"]
        self.assertEqual(
            found_culture_order,
            [
                ["02/01/2017", "212"],
                ["01/01/2017", "212"]
            ]
        )
        self.assertEqual(
            len(contents["cultures"]["02/01/2017"]["212"]["aerobic"]),
            1
        )
        found_fish = contents["cultures"]["02/01/2017"]["212"]["aerobic"]['2'][0]

        self.assertEqual(
            found_fish["id"],
            quick_fish.id
        )

        self.assertEqual(
            found_fish["lab_test_type"],
            quick_fish.get_display_name()
        )

        found_gram = contents["cultures"]["01/01/2017"]["212"]["anaerobic"]['1'][0]

        self.assertEqual(
            found_gram["id"],
            gram_stain.id
        )

        self.assertEqual(
            found_gram["lab_test_type"],
            gram_stain.get_display_name()
        )

    def test_retrieve_with_falsy_lab_number(self):
        # if lab number is None or "" we should group them together
        request = self.rf.get("/")
        url = reverse(
            "blood_culture_results-detail",
            kwargs=dict(pk=1),
            request=request
        )
        some_date = datetime.date(2017, 1, 1)
        patient, _ = self.new_patient_and_episode_please()

        gram_stain = emodels.GramStain.objects.create(
            date_ordered=some_date,
            patient=patient,
        )

        gram_stain.extras = dict(
            lab_number=None,
            aerobic=False,
            isolate=1
        )
        gram_stain.save()
        gram_stain.result.result = "Yeast"
        gram_stain.result.lab_test_id = gram_stain.id
        gram_stain.result.save()

        some_other_date = datetime.date(2017, 1, 1)
        quick_fish = emodels.QuickFISH.objects.create(
            date_ordered=some_other_date,
            patient=patient,
        )

        quick_fish.extras = dict(
            lab_number="",
            aerobic=False,
            isolate=1
        )
        quick_fish.save()
        quick_fish.result.result = "C. albicans"
        quick_fish.result.lab_test_id = quick_fish.id
        quick_fish.result.save()
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        contents = json.loads(result.content)
        self.assertEqual(
            len(contents["cultures"]["01/01/2017"][""]["anaerobic"]["1"]),
            2
        )


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
