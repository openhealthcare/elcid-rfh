"""
Unittests for elcid.api
"""
import json
import mock
import datetime

from opal.core.test import OpalTestCase
from elcid import models as elcid_models
from django.utils import timezone
from django.test import override_settings
from rest_framework.reverse import reverse

from elcid import models as emodels
from plugins.labtests.models import LabTest

from elcid.api import (
    BloodCultureResultApi, UpstreamBloodCultureApi
)
from elcid import api


class GenerateTimeSeriesTestCase(OpalTestCase):
    def test_generate_time_series(self):
        data = [
            dict(observation_value='1'),
            dict(observation_value='1'),
            dict(observation_value='2'),
            dict(observation_value='3'),
            dict(observation_value='1'),
        ]
        expected = [1, 1, 2, 3, 1]
        self.assertEqual(expected, api.generate_time_series(data))


class ExtractObservationValueTestCase(OpalTestCase):
    def test_extract_observation_value(self):
        inputs_to_expected_results = (
            ("<1", float(1),),
            ("1>", float(1),),
            (" 1 ", float(1),),
            ("< 1", float(1),),
            (" < 1", float(1),),
            (".1 ", None),
            ("0.1 ", 0.1),
            ("1E", None),
            ("'1'", None),
        )
        for input, expected in inputs_to_expected_results:
            self.assertEqual(api.extract_observation_value(input), expected)


class ToDateStrTestCase(OpalTestCase):
    def test_takes_first_ten_chars(self):
        self.assertEqual('First of A', api.to_date_str('First of April 1975'))


class DatetimeToStrTestCase(OpalTestCase):
    def test_to_str(self):
        dt = datetime.datetime(2017, 7, 4)
        self.assertEqual('04/07/2017 00:00:00', api.datetime_to_str(dt))


class ObservationsByDateTestCase(OpalTestCase):
    def test_observations_by_date(self):
        data = [
            dict(observation_datetime='04/07/2017', value='pos'),
            dict(observation_datetime='14/07/2017', value='neg')
        ]
        expected = [
            dict(observation_datetime='14/07/2017', value='neg'),
            dict(observation_datetime='04/07/2017', value='pos')
        ]
        self.assertEqual(expected, api.observations_by_date(data))


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
        some_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
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

        some_other_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
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
        contents = json.loads(result.content.decode('utf-8'))
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
        response = json.loads(
            self.client.get(self.url).content.decode('utf-8')
        )
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
        response = json.loads(
            self.client.get(self.url).content.decode('utf-8')
        )
        self.assertEqual(
            response["status"], "patient_not_found"
        )

    @override_settings(USE_UPSTREAM_DEMOGRAPHICS=True)
    @mock.patch("elcid.api.loader.load_demographics")
    def test_with_demographics_add_patient_found_upstream(
        self, load_demographics
    ):
        load_demographics.return_value = dict(first_name="Wilma")
        response = json.loads(
            self.client.get(self.url).content.decode('utf-8')
        )
        self.assertEqual(
            response["status"], "patient_found_upstream"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Wilma"
        )

    def test_patient_found(self):
        self.get_patient("Wilma", "1")
        response = json.loads(self.client.get(self.url).content.decode('utf-8'))
        self.assertEqual(
            response["status"], "patient_found_in_elcid"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Wilma"
        )

    def test_patient_found_with_full_stop(self):
        self.get_patient("Dot", "123.123")
        response = json.loads(
            self.client.get(self.get_url("123.123")).content.decode('utf-8')
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
            self.client.get(self.get_url("123%2F123")).content.decode('utf-8')
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
            self.client.get(self.get_url("123%23123")).content.decode('utf-8')
        )
        self.assertEqual(
            response["status"], "patient_found_in_elcid"
        )
        self.assertEqual(
            response["patient"]["demographics"][0]["first_name"], "Dot"
        )


class GetReferenceRangeTestCase(OpalTestCase):
    def test_clean_ref_range(self):
        self.assertEqual(
            api.get_reference_range("[ 2 - 3 ]"),
            dict(min="2", max="3")
        )

    def test_return_none_if_only_dash(self):
        self.assertIsNone(
            api.get_reference_range(" - ")
        )

    def test_return_none_if_more_than_one_dash(self):
        self.assertIsNone(
            api.get_reference_range("else -something - or")
        )

    def test_return_stripped_max_min(self):
        self.assertEqual(
            api.get_reference_range("2-3"),
            dict(min="2", max="3")
        )


class BloodCultureSetTestCase(OpalTestCase):
    def setUp(self):
        positive = datetime.date(2019, 5, 9)
        yesterday = positive - datetime.timedelta(1)
        patient, _ = self.new_patient_and_episode_please()
        self.bcs = emodels.BloodCultureSet.objects.create(
            date_ordered=yesterday,
            source="Hickman",
            lab_number="111",
            patient=patient
        )
        isolate = self.bcs.isolates.create(
            aerobic_or_anaerobic=emodels.BloodCultureIsolate.AEROBIC,
            consistency_token="111",
            date_positive=positive
        )
        isolate.gram_stain = "Gram -ve Rods"
        isolate.quick_fish = "Negative"
        isolate.save()
        request = self.rf.get("/")
        self.url = reverse(
            "blood_culture_set-detail",
            kwargs=dict(pk=self.bcs.id),
            request=request
        )
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )

    def test_retrieve_with_isolates(self):
        """
        Retrieve requests should return the isolates
        """
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, 200
        )
        expected = {
            'consistency_token': '',
            'created': None,
            'created_by_id': None,
            'date_ordered': datetime.date(2019, 5, 8),
            'id': 1,
            'isolates': [{
                'aerobic_or_anaerobic': 'Aerobic',
                'date_positive': datetime.date(2019, 5, 9),
                'blood_culture_set_id': 1,
                'consistency_token': '111',
                'created': None,
                'created_by_id': None,
                'gpc_staph': '',
                'gpc_strep': '',
                'gram_stain': 'Gram -ve Rods',
                'id': 1,
                'notes': '',
                'organism': '',
                'quick_fish': 'Negative',
                'sepsityper_organism': '',
                'resistance': [],
                'sensitivities': [],
                'updated': None,
                'updated_by_id': None
            }],
            'lab_number': '111',
            'patient_id': 1,
            'source': 'Hickman',
            'updated': None,
            'updated_by_id': None
        }
        self.assertEqual(response.data, expected)

    def test_retrieve_without_isolates(self):
        """
        Retrieve requests should return empty lists
        if there are no isolates
        """
        self.bcs.isolates.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, 200
        )
        expected = {
            'consistency_token': '',
            'created': None,
            'created_by_id': None,
            'date_ordered': datetime.date(2019, 5, 8),
            'id': 1,
            'isolates': [],
            'lab_number': '111',
            'patient_id': 1,
            'source': 'Hickman',
            'updated': None,
            'updated_by_id': None
        }
        self.assertEqual(response.data, expected)

    def test_update_with_isolates(self):
        """
        Updates should update normally but not change isolates
        """
        data = {
            'consistency_token': '',
            'created': None,
            'created_by_id': None,
            # Note we are changing date ordered so its 10th
            'date_ordered': "10/05/2019",
            'id': 1,
            'isolates': [{
                # Note we are changing aerobic to anaerobic
                'aerobic_or_anaerobic': 'Anerobic',
                'date_positive': "10/05/2019",
                'blood_culture_set_id': 1,
                'consistency_token': '111',
                'created': None,
                'created_by_id': None,
                'gpc_staph': '',
                'gpc_strep': '',
                'gram_stain': 'Gram -ve Rods',
                'id': 1,
                'notes': '',
                'organism': '',
                'quick_fish': 'Negative',
                'sepsityper_organism': '',
                'resistance': [],
                'sensitivities': [],
                'updated': None,
                'updated_by_id': None
            }],
            'lab_number': '111',
            'patient_id': 1,
            'source': 'Hickman',
            'updated': None,
            'updated_by_id': None
        }
        response = self.client.put(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(
            response.status_code, 202
        )
        bcs = emodels.BloodCultureSet.objects.get(id=1)
        isolate = bcs.isolates.get()
        self.assertEqual(
            isolate.aerobic_or_anaerobic, isolate.AEROBIC
        )
        self.assertEqual(
            isolate.date_positive, datetime.date(2019, 5, 9)
        )

    def test_update_with_empty_isolates(self):
        """
        Updates with no isolates should not remove isolates
        """
        data = {
            'consistency_token': '',
            'created': None,
            'created_by_id': None,
            # Note we have changed the date ordered
            'date_ordered': "10/05/2019",
            'id': 1,
            'isolates': [],
            'lab_number': '111',
            'patient_id': 1,
            'source': 'Hickman',
            'updated': None,
            'updated_by_id': None
        }
        response = self.client.put(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(
            response.status_code, 202
        )
        bcs = emodels.BloodCultureSet.objects.get(id=1)
        self.assertEqual(
            bcs.date_ordered, datetime.date(2019, 5, 10)
        )
        self.assertTrue(
            bcs.isolates.exists()
        )


class BloodCultureIsolateTestCase(OpalTestCase):
    def setUp(self):
        positive = datetime.date(2019, 5, 8)
        yesterday = positive - datetime.timedelta(1)
        patient, _ = self.new_patient_and_episode_please()
        self.bcs = emodels.BloodCultureSet.objects.create(
            date_ordered=yesterday,
            source="Hickman",
            lab_number="111",
            patient=patient
        )
        self.isolate = self.bcs.isolates.create(
            aerobic_or_anaerobic=emodels.BloodCultureIsolate.AEROBIC,
            consistency_token="111",
            date_positive=positive,
        )
        self.isolate.gram_stain = "Gram -ve Rods"
        self.isolate.quick_fish = "Negative"
        self.isolate.save()
        request = self.rf.get("/")
        self.detail_url = reverse(
            "blood_culture_isolate-detail",
            kwargs=dict(pk=1),
            request=request
        )
        self.list_url = reverse(
            "blood_culture_isolate-list",
            request=request
        )
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )

    def test_retrieve(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(
            response.status_code, 200
        )
        expected = {
            'notes': '',
            'resistance': [],
            'sepsityper_organism': '',
            'gpc_strep': '',
            'created_by_id': None,
            'updated': None,
            'id': self.isolate.id,
            'gram_stain': 'Gram -ve Rods',
            'date_positive': datetime.date(2019, 5, 8),
            'sensitivities': [],
            'updated_by_id': None,
            'quick_fish': 'Negative',
            'blood_culture_set_id': 1,
            'gpc_staph': '',
            'created': None,
            'organism': '',
            'consistency_token': '111',
            'aerobic_or_anaerobic': 'Aerobic'
        }
        self.assertEqual(
            response.data, expected
        )

    def test_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(
            response.status_code, 200
        )
        expected = [{
            'notes': '',
            'resistance': [],
            'date_positive': datetime.date(2019, 5, 8),
            'gpc_strep': '',
            'created_by_id': None,
            'updated': None,
            'id': self.isolate.id,
            'gram_stain': 'Gram -ve Rods',
            'sensitivities': [],
            'sepsityper_organism': '',
            'updated_by_id': None,
            'quick_fish': 'Negative',
            'blood_culture_set_id': 1,
            'gpc_staph': '',
            'created': None,
            'organism': '',
            'consistency_token': '111',
            'aerobic_or_anaerobic': 'Aerobic'
        }]
        self.assertEqual(
            response.data, expected
        )

    def test_create(self):
        data = {
            'notes': '',
            'resistance': [],
            'sepsityper_organism': '',
            'gpc_strep': '',
            'created_by_id': None,
            'updated': None,
            'gram_stain': 'Gram -ve Rods',
            'sensitivities': [],
            'updated_by_id': None,
            'quick_fish': 'Negative',
            'blood_culture_set_id': 1,
            'gpc_staph': '',
            'created': None,
            'organism': '',
            'consistency_token': '111',
            'aerobic_or_anaerobic': 'Anerobic'
        }
        response = self.client.post(
            self.list_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(
            response.status_code, 201
        )
        self.assertEqual(
            self.bcs.isolates.count(), 2
        )
        new_isolate = self.bcs.isolates.exclude(id=self.isolate.id).get()
        self.assertEqual(
            new_isolate.aerobic_or_anaerobic, 'Anerobic'
        )

    def test_update(self):
        data = {
            'id': self.isolate.id,
            'notes': '',
            'resistance': [],
            'gpc_strep': '',
            'created_by_id': None,
            'updated': None,
            'gram_stain': 'Gram -ve Rods',
            'sensitivities': [],
            'updated_by_id': None,
            'quick_fish': 'Negative',
            'sepsityper_organism': '',
            'blood_culture_set_id': 1,
            'gpc_staph': '',
            'created': None,
            'organism': '',
            'consistency_token': '111',
            'aerobic_or_anaerobic': 'Anerobic'
        }
        response = self.client.put(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(
            response.status_code, 202
        )
        reloaded_isolate = self.bcs.isolates.get()
        self.assertEqual(
            reloaded_isolate.aerobic_or_anaerobic, 'Anerobic'
        )

@override_settings(NEW_LAB_TEST_SUMMARY_DISPLAY=True)
class LabTestSummaryTestCase(OpalTestCase):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        self._lab_number = 0
        self.url = ""
        request = self.rf.get("/")
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )
        self.url = reverse(
            "infection_service_summary_api-detail",
            kwargs=dict(pk=self.patient.id),
            request=request
        )

    def get_lab_number(self):
        self._lab_number += 1
        return str(self._lab_number)

    def create_blood_count(self, *some_dts, patient=None):
        if patient is None:
            patient = self.patient

        for some_dt in some_dts:
            lab_test = patient.lab_tests.create(
                datetime_ordered=some_dt,
                test_name="FULL BLOOD COUNT",
                lab_number=self.get_lab_number()
            )
            lab_test.observation_set.create(
                observation_datetime=some_dt,
                observation_name="WBC",
                reference_range="1.7 - 7.5",
                observation_value="1.8",
                units="g/l",
            )
            lab_test.observation_set.create(
                observation_datetime=some_dt,
                observation_name="Lymphocytes",
                reference_range="1 - 4",
                observation_value="1",
                units="10",
            )
            lab_test.observation_set.create(
                observation_datetime=some_dt,
                observation_name="Neutrophils",
                reference_range="1.7 - 7.5",
                observation_value="2",
                units="10",
            )

    def create_clotting_screen(self, dt_to_value, patient=None):
        if patient is None:
            patient = self.patient

        for some_dt, value in dt_to_value.items():
            lab_test = patient.lab_tests.create(
                datetime_ordered=some_dt,
                test_name="CLOTTING SCREEN",
                lab_number=self.get_lab_number()
            )
            lab_test.observation_set.create(
                observation_datetime=some_dt,
                observation_name="INR",
                reference_range="0.9 - 1.12",
                observation_value=value,
                units="Ratio",
            )

    def create_c_reactive_protein(self, dt_to_value, patient=None):
        if patient is None:
            patient = self.patient
        for some_dt, value in dt_to_value.items():
            lab_test = patient.lab_tests.create(
                datetime_ordered=some_dt,
                test_name="C REACTIVE PROTEIN",
                lab_number=self.get_lab_number()
            )
            lab_test.observation_set.create(
                observation_datetime=some_dt,
                observation_name="C Reactive Protein",
                reference_range="0 - 5",
                observation_value=value,
                units="mg/L",
            )

    def test_vanilla_check(self):
        dt_1 = datetime.datetime(2019, 6, 5, 10, 10)
        dt_2 = datetime.datetime(2019, 6, 4, 10, 10)
        self.create_blood_count(dt_1, dt_2)
        self.create_clotting_screen({
            dt_1: "1.2", dt_2: "1.2"
        })
        self.create_c_reactive_protein({
            dt_1: "1.0", dt_2: "1.0"
        })

        result = self.client.get(self.url)
        expected = {
            'obs_values': [
                {
                    'latest_results': {'04/06/2019': 1.8, '05/06/2019': 1.8},
                    'name': 'WBC',
                    'reference_range': {'max': '7.5', 'min': '1.7'},
                    'units': 'g/l'
                },
                {
                    'latest_results': {'04/06/2019': 1.0, '05/06/2019': 1.0},
                    'name': 'Lymphocytes',
                    'reference_range': {'max': '4', 'min': '1'},
                    'units': '10'
                },
                {
                    'latest_results': {'04/06/2019': 2.0, '05/06/2019': 2.0},
                    'name': 'Neutrophils',
                    'reference_range': {'max': '7.5', 'min': '1.7'},
                    'units': '10'
                },
                {
                    'latest_results': {'04/06/2019': 1.2, '05/06/2019': 1.2},
                    'name': 'INR',
                    'reference_range': {'max': '1.12', 'min': '0.9'},
                    'units': 'Ratio'
                },
                {
                    'latest_results': {'04/06/2019': 1.0, '05/06/2019': 1.0},
                    'name': 'C Reactive Protein',
                    'reference_range': {'max': '5', 'min': '0'},
                    'units': 'mg/L'
                }
            ],
            'recent_dates': [
                datetime.date(2019, 6, 4),
                datetime.date(2019, 6, 5),
                None,
                None,
                None,
            ]
        }
        self.assertEqual(result.data, expected)

    def test_multiple_results_on_the_same_day(self):
        """
        We should use the latest date
        """
        dt_1 = datetime.datetime(2019, 6, 4, 10, 10)
        dt_2 = datetime.datetime(2019, 6, 4, 12, 10)
        dt_3 = datetime.datetime(2019, 6, 4, 11, 10)
        self.create_clotting_screen({
            dt_1: "1.1", dt_2: "1.3", dt_3: "1.2"
        })
        result = self.client.get(self.url)
        expected = {
            'obs_values': [
                {
                    'latest_results': {'04/06/2019': 1.3},
                    'name': 'INR',
                    'reference_range': {'max': '1.12', 'min': '0.9'},
                    'units': 'Ratio'
                }
            ],
            'recent_dates': [datetime.date(2019, 6, 4), None, None, None, None]
        }
        self.assertEqual(result.data, expected)

    def test_results_date_crunching(self):
        """
        we should get the last 5 results for all lab tests
        then the last 5 dates of all dates related to lab tests
        e.g.
        CS 1 Jan, 2 Jan, 9 Jan, 10 Jan, 11 Jan
        CRP 5 Jan, 6 Jan, 7 Jan, 8 Jan, 9 Jan

        that we should display those tests but with recent dates
        of 7 Jan, 8 Jan, 9 Jan, 10 Jan , 11 Jan in that order
        """

        dt_1 = datetime.datetime(2019, 6, 1)
        dt_2 = datetime.datetime(2019, 6, 2)
        dt_3 = datetime.datetime(2019, 6, 5)
        dt_4 = datetime.datetime(2019, 6, 6)
        dt_5 = datetime.datetime(2019, 6, 7)
        dt_6 = datetime.datetime(2019, 6, 8)
        dt_7 = datetime.datetime(2019, 6, 9)
        dt_8 = datetime.datetime(2019, 6, 10)
        dt_9 = datetime.datetime(2019, 6, 11)

        self.create_clotting_screen({
            dt_1: "1.1", dt_2: "1.2", dt_3: "1.3", dt_8: "1.8", dt_9: "1.9"
        })
        self.create_c_reactive_protein({
            dt_4: "1.4", dt_5: "1.5", dt_6: "1.6", dt_7: "1.7", dt_8: "1.8"
        })
        expected = {
            'obs_values':
                [
                    {
                        'latest_results': {
                            '01/06/2019': 1.1,
                            '02/06/2019': 1.2,
                            '05/06/2019': 1.3,
                            '10/06/2019': 1.8,
                            '11/06/2019': 1.9
                        },
                        'name': 'INR',
                        'reference_range': {
                            'max': '1.12', 'min': '0.9'
                        },
                        'units': 'Ratio'
                    },
                    {
                        'latest_results': {
                            '06/06/2019': 1.4,
                            '07/06/2019': 1.5,
                            '08/06/2019': 1.6,
                            '09/06/2019': 1.7,
                            '10/06/2019': 1.8
                        },
                        'name': 'C Reactive Protein',
                        'reference_range': {
                            'max': '5', 'min': '0'
                        },
                        'units': 'mg/L'
                    }
                ],
                'recent_dates': [
                    datetime.date(2019, 6, 7),
                    datetime.date(2019, 6, 8),
                    datetime.date(2019, 6, 9),
                    datetime.date(2019, 6, 10),
                    datetime.date(2019, 6, 11),
                ]}

        result = self.client.get(self.url)
        self.assertEqual(result.data, expected)

    def test_ignores_strings(self):
        self.create_clotting_screen({
            datetime.datetime(2019, 6, 4, 12, 10): "Pending"
        })
        result = self.client.get(self.url)
        expected = {
             'obs_values': [],
             'recent_dates': [None, None, None, None, None]
        }
        self.assertEqual(result.data, expected)

    def test_ignore_strings_same_date(self):
        dt_1 = datetime.datetime(2019, 6, 4, 12, 10)
        dt_2 = datetime.datetime(2019, 6, 4, 11, 10)
        self.create_clotting_screen({
            dt_1: "Pending", dt_2: "1.3"
        })

    def test_handles_no_tests(self):
        result = self.client.get(self.url)
        expected = {
             'obs_values': [],
             'recent_dates': [None, None, None, None, None]
        }
        self.assertEqual(result.data, expected)

