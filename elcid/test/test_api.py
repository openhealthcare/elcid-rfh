"""
Unittests for elcid.api
"""
import json
from unittest import mock
import datetime

from opal.core.test import OpalTestCase
from django.utils import timezone
from django.test import override_settings
from rest_framework.reverse import reverse

from elcid import models as emodels
from elcid.api import (
    UpstreamBloodCultureApi, LabTestResultsView,
    InfectionServiceTestSummaryApi
)


class LabTestResultsViewTestCase(OpalTestCase):

    def test_get_non_comments_for_patient(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'BLOOD TEST'
        })

        api = LabTestResultsView()
        tests = api.get_non_comments_for_patient(patient)
        self.assertEqual(1, len(tests))
        self.assertEqual('BLOOD TEST', tests[0].test_name)

    def test_get_non_comments_for_patient_excludes_comments(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'BLOOD TEST'
        })
        patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 16, 4, 15, 10),
            'test_name': 'COMMENT'
        })

        api = LabTestResultsView()
        tests = api.get_non_comments_for_patient(patient)
        self.assertEqual(1, len(tests))
        self.assertEqual('BLOOD TEST', tests[0].test_name)


    def test_group_tests(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'BLOOD TEST'
        })
        patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 16, 4, 15, 10),
            'test_name': 'BLOOD TEST'
        })
        patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 16, 4, 15, 10),
            'test_name': 'HIV TEST'
        })

        api = LabTestResultsView()
        grouped = api.group_tests(patient.lab_tests.all())
        self.assertEqual(2, len(grouped['BLOOD TEST']))
        self.assertEqual(1, len(grouped['HIV TEST']))

    def test_is_long_form_always_show(self):
        api = LabTestResultsView()
        self.assertFalse(api.is_long_form("TACROLIMUS", None))

    def test_is_long_form_long_form(self):
        patient, _ = self.new_patient_and_episode_please()
        test = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'BLOOD TEST'
        })

        test.observation_set.create(**{
            'observation_value': 'No Growth Seen'
        })

        api = LabTestResultsView()

        self.assertTrue(api.is_long_form('BLOOD TEST', [test]))

    def test_is_long_form_not_long_form(self):
        patient, _ = self.new_patient_and_episode_please()
        test = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'LFT'
        })

        test.observation_set.create(**{
            'observation_value': '3'
        })

        api = LabTestResultsView()

        self.assertFalse(api.is_long_form('LFT', [test]))

    def test_is_empty_value(self):
        api = LabTestResultsView()
        self.assertTrue(api.is_empty_value(None))

    def test_is_empty_value_ignores_dash(self):
        api = LabTestResultsView()
        self.assertTrue(api.is_empty_value(' - '))

    def test_is_empty_value_ignores_hash(self):
        api = LabTestResultsView()
        self.assertTrue(api.is_empty_value(' # '))

    def test_is_empty_value_knows_non_empty_value(self):
        api = LabTestResultsView()
        self.assertFalse(api.is_empty_value(' 23 '))

    def test_display_class_too_high(self):
        patient, _ = self.new_patient_and_episode_please()
        test = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'LFT'
        })

        observation = test.observation_set.create(**{
            'observation_value': '3',
            'reference_range'  : '1 - 2'
        })

        api = LabTestResultsView()

        self.assertEqual('too-high', api.display_class_for_observation(observation))

    def test_display_class_too_low(self):
        patient, _ = self.new_patient_and_episode_please()
        test = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'LFT'
        })

        observation = test.observation_set.create(**{
            'observation_value': '3',
            'reference_range'  : '10 - 20'
        })

        api = LabTestResultsView()

        self.assertEqual('too-low', api.display_class_for_observation(observation))

    def test_display_class_empty(self):
        patient, _ = self.new_patient_and_episode_please()
        test = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'LFT'
        })

        observation = test.observation_set.create(**{
            'observation_value': '3',
            'reference_range'  : '1 - 10'
        })

        api = LabTestResultsView()

        self.assertEqual('', api.display_class_for_observation(observation))

    def test_display_class_obs_value_none(self):
        patient, _ = self.new_patient_and_episode_please()
        test = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name': 'LFT'
        })

        observation = test.observation_set.create(**{
            'observation_value': 'Pending',
            'reference_range'  : '1 - 10'
        })

        api = LabTestResultsView()

        self.assertEqual('', api.display_class_for_observation(observation))

    def test_serialise_tabular_instances(self):
        patient, _ = self.new_patient_and_episode_please()
        test = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name'       : 'FULL BLOOD COUNT',
            'lab_number'      : '123'
        })
        test.observation_set.create(**{
            'observation_name' : 'WBC',
            'observation_value': '3',
            'reference_range'  : '1 - 10'
        })
        test.observation_set.create(**{
            'observation_name' : 'RBC',
            'observation_value': '13',
            'reference_range'  : '10 - 100'
        })

        test2 = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 10, 4, 15, 10),
            'test_name'       : 'FULL BLOOD COUNT',
            'lab_number'      : '121'
        })
        test2.observation_set.create(**{
            'observation_name' : 'WBC',
            'observation_value': '20',
            'reference_range'  : '1 - 10'
        })
        test2.observation_set.create(**{
            'observation_name' : 'RBC',
            'observation_value': '123',
            'reference_range'  : '10 - 100'
        })

        expected_datetimes = ['10/06/2019 04:15:10','17/06/2019 04:15:10']
        expected_observation_names = ['RBC', 'WBC']
        expected_lab_numbers = {
            '10/06/2019 04:15:10': '121',
            '17/06/2019 04:15:10': '123'
        }
        expected_observation_ranges = {'WBC': '1 - 10', 'RBC': '10 - 100'}
        expected_observation_series = {
            'WBC': {
                '10/06/2019 04:15:10': {
                    'value': '20',
                    'range': '1 - 10',
                    'display_class': 'too-high'
                },
                '17/06/2019 04:15:10': {
                    'value': '3',
                    'range': '1 - 10',
                    'display_class': ''
                }
            },
            'RBC': {
                '10/06/2019 04:15:10': {
                    'value': '123',
                    'range': '10 - 100',
                    'display_class': 'too-high'
                },
                '17/06/2019 04:15:10': {
                    'value': '13',
                    'range': '10 - 100',
                    'display_class': ''
                }
            }
        }

        api = LabTestResultsView()
        serialised = api.serialise_tabular_instances(patient.lab_tests.all())

        self.assertEqual(expected_datetimes, serialised['test_datetimes'])
        self.assertEqual(expected_observation_names, serialised['observation_names'])
        self.assertEqual(expected_lab_numbers, serialised['lab_numbers'])
        self.assertEqual(expected_observation_ranges, serialised['observation_ranges'])
        self.assertEqual(expected_observation_series, serialised['observation_series'])

    def test_serialise_long_form_instance(self):
        patient, _ = self.new_patient_and_episode_please()
        test  = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 10, 4, 15, 10),
            'test_name'       : 'BLOOD CULTURE',
            'lab_number'      : '121'
        })
        test.observation_set.create(**{
            'observation_name' : 'ORGANISM',
            'observation_value': 'Staph. Aureus',
        })

        api = LabTestResultsView()

        serialised = api.serialise_long_form_instance(test)

        self.assertEqual('121', serialised['lab_number'])

    def test_retrieve(self):
        patient, _ = self.new_patient_and_episode_please()
        test  = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2017, 6, 10, 4, 15, 10),
            'test_name'       : 'BLOOD CULTURE',
            'lab_number'      : '121'
        })
        test.observation_set.create(**{
            'observation_name' : 'ORGANISM',
            'observation_value': 'Staph. Aureus',
        })
        test2 = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 17, 4, 15, 10),
            'test_name'       : 'FULL BLOOD COUNT',
            'lab_number'      : '123'
        })
        test2.observation_set.create(**{
            'observation_name' : 'WBC',
            'observation_value': '3',
            'reference_range'  : '1 - 10'
        })
        test2.observation_set.create(**{
            'observation_name' : 'RBC',
            'observation_value': '13',
            'reference_range'  : '10 - 100'
        })

        test3 = patient.lab_tests.create(**{
            'datetime_ordered': datetime.datetime(2019, 6, 10, 4, 15, 10),
            'test_name'       : 'FULL BLOOD COUNT',
            'lab_number'      : '121'
        })
        test3.observation_set.create(**{
            'observation_name' : 'WBC',
            'observation_value': '20',
            'reference_range'  : '1 - 10'
        })
        test3.observation_set.create(**{
            'observation_name' : 'RBC',
            'observation_value': '123',
            'reference_range'  : '10 - 100'
        })

        expected_FBC_observation_series = {
            'WBC': {
                '10/06/2019 04:15:10': {
                    'value': '20',
                    'range': '1 - 10',
                    'display_class': 'too-high'
                },
                '17/06/2019 04:15:10': {
                    'value': '3',
                    'range': '1 - 10',
                    'display_class': ''
                }
            },
            'RBC': {
                '10/06/2019 04:15:10': {
                    'value': '123',
                    'range': '10 - 100',
                    'display_class': 'too-high'
                },
                '17/06/2019 04:15:10': {
                    'value': '13',
                    'range': '10 - 100',
                    'display_class': ''
                }
            }
        }

        expected_BC_observations = [
            {'name': 'ORGANISM', 'value': 'Staph. Aureus'}
        ]

        expected_test_order = ['FULL BLOOD COUNT', 'BLOOD CULTURE']

        api = LabTestResultsView()
        result = api.retrieve(None, pk=patient.id)

        data = json.loads(result.content.decode('UTF-8'))

        self.assertEqual(expected_test_order, data['test_order'])
        self.assertEqual(
            expected_FBC_observation_series,
            data['tests']['FULL BLOOD COUNT']['instances']['observation_series'])
        self.assertEqual(
            expected_BC_observations,
            data['tests']['BLOOD CULTURE']['instances'][0]['observations']
        )


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
        dt_1 = timezone.make_aware(datetime.datetime(2019, 6, 5, 10, 10))
        dt_2 = timezone.make_aware(datetime.datetime(2019, 6, 4, 10, 10))
        self.create_blood_count(dt_1, dt_2)
        self.create_clotting_screen({
            dt_1: "1.2", dt_2: "1.2"
        })
        self.create_c_reactive_protein({
            dt_1: "1.0", dt_2: "1.0"
        })

        result = self.client.get(self.url)
        expected = {
            'ticker': [],
            'obs_values': [
                {
                    'latest_results': {'04/06/2019': 1.8, '05/06/2019': 1.8},
                    'name': 'WBC',
                    'reference_range': {'max': 7.5, 'min': 1.7},
                    'units': 'g/l'
                },
                {
                    'latest_results': {'04/06/2019': 1.0, '05/06/2019': 1.0},
                    'name': 'Lymphocytes',
                    'reference_range': {'max': 4, 'min': 1},
                    'units': '10'
                },
                {
                    'latest_results': {'04/06/2019': 2.0, '05/06/2019': 2.0},
                    'name': 'Neutrophils',
                    'reference_range': {'max': 7.5, 'min': 1.7},
                    'units': '10'
                },
                {
                    'latest_results': {'04/06/2019': 1.2, '05/06/2019': 1.2},
                    'name': 'INR',
                    'reference_range': {'max': 1.12, 'min': 0.9},
                    'units': 'Ratio'
                },
                {
                    'latest_results': {'04/06/2019': 1.0, '05/06/2019': 1.0},
                    'name': 'C Reactive Protein',
                    'reference_range': {'max': 5, 'min': 0},
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
        dt_1 = timezone.make_aware(datetime.datetime(2019, 6, 4, 10, 10))
        dt_2 = timezone.make_aware(datetime.datetime(2019, 6, 4, 12, 10))
        dt_3 = timezone.make_aware(datetime.datetime(2019, 6, 4, 11, 10))
        self.create_clotting_screen({
            dt_1: "1.1", dt_2: "1.3", dt_3: "1.2"
        })
        result = self.client.get(self.url)
        expected = {
            'ticker': [],
            'obs_values': [
                {
                    'latest_results': {'04/06/2019': 1.3},
                    'name': 'INR',
                    'reference_range': {'max': 1.12, 'min': 0.9},
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

        dt_1 = timezone.make_aware(datetime.datetime(2019, 6, 1))
        dt_2 = timezone.make_aware(datetime.datetime(2019, 6, 2))
        dt_3 = timezone.make_aware(datetime.datetime(2019, 6, 5))
        dt_4 = timezone.make_aware(datetime.datetime(2019, 6, 6))
        dt_5 = timezone.make_aware(datetime.datetime(2019, 6, 7))
        dt_6 = timezone.make_aware(datetime.datetime(2019, 6, 8))
        dt_7 = timezone.make_aware(datetime.datetime(2019, 6, 9))
        dt_8 = timezone.make_aware(datetime.datetime(2019, 6, 10))
        dt_9 = timezone.make_aware(datetime.datetime(2019, 6, 11))

        self.create_clotting_screen({
            dt_1: "1.1", dt_2: "1.2", dt_3: "1.3", dt_8: "1.8", dt_9: "1.9"
        })
        self.create_c_reactive_protein({
            dt_4: "1.4", dt_5: "1.5", dt_6: "1.6", dt_7: "1.7", dt_8: "1.8"
        })
        expected = {
            'ticker': [],
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
                            'max': 1.12, 'min': 0.9
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
                            'max': 5, 'min': 0
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
            timezone.make_aware(datetime.datetime(2019, 6, 4, 12, 10)): "Pending"
        })
        result = self.client.get(self.url)
        expected = {
            'ticker': [],
             'obs_values': [],
             'recent_dates': [None, None, None, None, None]
        }
        self.assertEqual(result.data, expected)

    def test_ignore_strings_same_date(self):
        dt_1 = timezone.make_aware(datetime.datetime(2019, 6, 4, 12, 10))
        dt_2 = timezone.make_aware(datetime.datetime(2019, 6, 4, 11, 10))
        self.create_clotting_screen({
            dt_1: "Pending", dt_2: "1.3"
        })

    def test_handles_no_tests(self):
        result = self.client.get(self.url)
        expected = {
            'ticker': [],
             'obs_values': [],
             'recent_dates': [None, None, None, None, None]
        }
        self.assertEqual(result.data, expected)

    def test_get_procalcitonin(self):
        api = InfectionServiceTestSummaryApi()

        mock_observation = mock.MagicMock(name='Mock observation')
        mock_observation.observation_value = "0.61~PCT 0.5-1.99       Suggestive of the presence of~bacterial infection. Please interpret within the~clinical picture. Consider repeat in 24-48 hours."

        self.assertEqual(
            "0.61",
            api.get_PROCALCITONIN_Procalcitonin(mock_observation)
        )

    def test_get_observation_value_calls_getter(self):
        api = InfectionServiceTestSummaryApi()

        mock_observation = mock.MagicMock(name='Mock observation')
        mock_observation.observation_name = 'Procalcitonin'
        mock_observation.observation_value = 'ONE MILLION~TESTS'
        mock_observation.test.test_name = 'PROCALCITONIN'

        self.assertEqual(
            "ONE MILLION",
            api.get_observation_value(mock_observation)
        )

    def test_get_observation_value_default(self):
        api = InfectionServiceTestSummaryApi()

        mock_observation = mock.MagicMock(name='Mock observation')
        mock_observation.value_numeric = 483

        self.assertEqual(
            483,
            api.get_observation_value(mock_observation)
        )
