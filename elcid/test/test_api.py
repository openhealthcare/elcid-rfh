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

    def test_format_sensitivities_and_resistances_sensitivities(self):
        some_str = "~ Teicoplanin S~ Vancomycin S"
        expected = dict(
            sensitive=["Teicoplanin", "Vancomycin"],
            resistant=[]
        )
        self.assertEqual(
            self.api.format_sensitivities_and_resistances(some_str),
            expected
        )

    def test_format_sensitivities_and_resistances_sensitivity(self):
        some_str = "~ Colistin (Polymixin) S~~"
        expected = dict(
            sensitive=["Colistin (Polymixin)"],
            resistant=[]
        )
        self.assertEqual(
            self.api.format_sensitivities_and_resistances(some_str),
            expected
        )

    def test_format_blood_culture_anaerobic(self):
        some_str = "1) After less than 24 hours Acinetobacter baumannii~ \
Isolated from aerobic bottle~2) After less than 24 hours \
Staphylococcus epidermidis~~ 2)~ Teicoplanin S~ Vancomycin S~~"
        expected = {
            "Aerobic": {
                "text": [
                    "After less than 24 hours Acinetobacter baumannii",
                    "Isolated from aerobic bottle"
                ],
                "sensitive": [],
                "resistant": []
            },
            "Anaerobic": {
                "text": [
                    "After less than 24 hours Staphylococcus epidermidis"
                ],
                "sensitive": ["Teicoplanin", "Vancomycin"],
                "resistant": []
            }
        }
        self.assertEqual(
            self.api.format_blood_culture(some_str),
            expected
        )

    def test_format_blood_culture_aerobic(self):
        some_str = "1) After less than 24 hours Escherichia coli~ Aerobic + \
anaerobic bottles~~ 1)~ Amoxicillin S~ Gentamicin S~ Temocillin S~~"
        expected = {
            "Aerobic": {
                "text": [
                    "After less than 24 hours Escherichia coli",
                    "Aerobic + anaerobic bottles"
                ],
                "sensitive": ["Amoxicillin", "Gentamicin", "Temocillin"],
                "resistant": []
            },
            "Anaerobic": {
                "text": [],
                "sensitive": [],
                "resistant": []
            }
        }
        found = self.api.format_blood_culture(some_str)
        self.assertEqual(found, expected)

    def test_format_blood_culture_resistant(self):
        some_str = "1) From aerobic bottle only Staphylococcus aureus~ after \
less than 24 hours of incubation.~~ 1)~ Erythromycin S~ Flucloxacillin S~ \
Penicillin R~~"
        expected = {
            "Aerobic": {
                "text": [
                    "From aerobic bottle only Staphylococcus aureus",
                    "after less than 24 hours of incubation."
                ],
                "sensitive": ["Erythromycin", "Flucloxacillin"],
                "resistant": ["Penicillin"]
            },
            "Anaerobic": {
                "text": [],
                "sensitive": [],
                "resistant": []
            }
        }
        found = self.api.format_blood_culture(some_str)
        self.assertEqual(found, expected)


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
        self.url = reverse(
            "demographics_search-detail",
            kwargs=dict(pk=1),
            request=request
        )
        # initialise the property
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=False)
    def test_without_demographics_add_patient_not_found(self):
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_not_found"
        )

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=True)
    @mock.patch("elcid.api.get_api")
    def test_with_demographics_add_patient_not_found(self, get_api):
        get_api().demographics.return_value = None
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_not_found"
        )

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=True)
    @mock.patch("elcid.api.get_api")
    def test_with_demographics_add_patient_found_upstream(self, get_api):
        get_api().demographics.return_value = dict(first_name="Wilma")
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_found_upstream"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Wilma"
        )

    def test_patient_found(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Wilma",
            hospital_number="1"
        )
        response = json.loads(self.client.get(self.url).content)
        self.assertEqual(
            response["status"], "patient_found_in_elcid"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Wilma"
        )
