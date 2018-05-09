import json
import mock
import datetime
from opal.core.test import OpalTestCase
from rest_framework.reverse import reverse
from elcid.api import (
    BloodCultureResultApi, UpstreamBloodCultureApi
)
from elcid import models as emodels
from django.test import override_settings


class UpstreamBloodCultureApiTestCase(OpalTestCase):
    def setUp(self):
        self.api = UpstreamBloodCultureApi()

    def test_no_growth_observations_present(self):
        obs = [
            dict(observation_name="Aerobic bottle culture"),
            dict(observation_name="Anaerobic bottle culture"),
        ]
        self.assertTrue(self.api.no_growth_observations(obs))

    def test_no_growth_observations_not_present(self):
        obs = [
            dict(observation_name="something"),
            dict(observation_name="Anaerobic bottle culture"),
        ]
        self.assertFalse(self.api.no_growth_observations(obs))


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
            datetime_ordered=some_date,
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
            datetime_ordered=some_other_date,
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
        self.assertEqual(len(contents["cultures"]["01/01/2017"]), 1)
        results = contents["cultures"]["01/01/2017"][""]["anaerobic"]["1"]
        self.assertEqual(
            [i["id"] for i in results],
            [gram_stain.id, quick_fish.id]

        )


class DemographicsSearchTestCase(OpalTestCase):
    def setUp(self):
        super(DemographicsSearchTestCase, self).setUp()
        request = self.rf.get("/")
        self.raw_url = reverse(
            "demographics_search-list",
            request=request
        )
        self.url = "{}?hospital_number=1".format(self.raw_url)
        # initialise the property
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )

    def get_url(self, hospital_number):
        return "{}?hospital_number={}".format(
            self.raw_url, hospital_number
        )

    def get_patient(self, name, hospital_number):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name=name,
            hospital_number=hospital_number
        )
        return patient

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=False)
    def test_without_demographics_add_patient_not_found(self):
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_not_found"
        )

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=True)
    def test_without_hospital_number(self):
        self.assertEqual(self.client.get(self.raw_url).status_code, 400)

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=True)
    @mock.patch("elcid.api.loader.load_demographics")
    def test_with_demographics_add_patient_not_found(
        self, load_demographics
    ):
        load_demographics.return_value = None
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_not_found"
        )

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=True)
    @mock.patch("elcid.api.loader.load_demographics")
    def test_with_demographics_add_patient_found_upstream(
        self, load_demographics
    ):
        load_demographics.return_value = dict(first_name="Wilma")
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_found_upstream"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Wilma"
        )

    def test_patient_found(self):
        self.get_patient("Wilma", "1")
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_found_in_elcid"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Wilma"
        )

    def test_patient_found_with_full_stop(self):
        self.get_patient("Dot", "123.123")
        response = json.loads(
            self.client.get(self.get_url("123.123")).content
        )
        self.assertEqual(
            response["status"], "patient_found_in_elcid"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Dot"
        )

    def test_patient_found_with_forward_slash(self):
        self.get_patient("Dot", "123/123")
        response = json.loads(
            self.client.get(self.get_url("123%2F123")).content
        )
        self.assertEqual(
            response["status"], "patient_found_in_elcid"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Dot"
        )

    def test_patient_found_with_hash(self):
        self.get_patient("Dot", "123#123")
        response = json.loads(
            self.client.get(self.get_url("123%23123")).content
        )
        self.assertEqual(
            response["status"], "patient_found_in_elcid"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Dot"
        )
