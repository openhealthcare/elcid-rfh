import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from opal.models import Patient
from plugins.labtests import models


class LabTestTestCase(OpalTestCase):
    def setUp(self):
        self.api_dict = {
            "clinical_info":  'testing',
            "datetime_ordered": "17/07/2015 04:15:10",
            "external_identifier": "11111",
            "site": u'^&        ^',
            "status": "Sucess",
            "test_code": "AN12",
            "test_name": "Anti-CV2 (CRMP-5) antibodies",
            "observations": [{
                "last_updated": "18/07/2015 04:15:10",
                "observation_datetime": "19/07/2015 04:15:10",
                "observation_name": "Aerobic bottle culture",
                "observation_number": "12312",
                "observation_value": "123",
                "reference_range": "3.5 - 11",
                "units": "g"
            }]
        }
        self.patient, _ = self.new_patient_and_episode_please()

    def create_lab_test(self):
        lt = self.patient.lab_tests.create(**{
            "clinical_info":  'testing',
            "datetime_ordered": datetime.datetime(2015, 6, 17, 4, 15, 10),
            "lab_number": "11111",
            "site": u'^&        ^',
            "status": "Sucess",
            "test_code": "AN12",
            "test_name": "Anti-CV2 (CRMP-5) antibodies",
        })

        lt.observation_set.create(
            last_updated=datetime.datetime(2015, 6, 18, 4, 15, 10),
            observation_datetime=datetime.datetime(2015, 4, 15, 4, 15, 10),
            observation_number="12312",
            reference_range="3.5 - 11",
            units="g",
            observation_value="234",
            observation_name="Aerobic bottle culture"
        )
        return lt

    def test_update_from_api_dict_simple(self):
        lt = models.LabTest()
        lt.update_from_api_dict(self.patient, self.api_dict)
        self.assertEqual(
            lt.patient, self.patient
        )
        self.assertEqual(
            lt.clinical_info, 'testing'
        )
        self.assertEqual(
            lt.datetime_ordered,
            timezone.make_aware(datetime.datetime(
                2015, 7, 17, 4, 15, 10
            ))
        )
        self.assertEqual(
            lt.lab_number, '11111'
        )
        self.assertEqual(
            lt.status, 'Sucess'
        )
        self.assertEqual(
            lt.test_code, 'AN12'
        )
        self.assertEqual(
            lt.test_name, 'Anti-CV2 (CRMP-5) antibodies'
        )

        self.assertEqual(
            lt.site, '^&        ^'
        )

        obs = lt.observation_set.get()
        self.assertEqual(
            obs.last_updated,
            timezone.make_aware(datetime.datetime(
                2015, 7, 18, 4, 15, 10
            ))
        )
        self.assertEqual(
            obs.observation_datetime,
            timezone.make_aware(datetime.datetime(
                2015, 7, 19, 4, 15, 10
            ))
        )
        self.assertEqual(
            obs.observation_name,
            "Aerobic bottle culture"
        )
        self.assertEqual(
            obs.observation_number,
            "12312"
        )
        self.assertEqual(
            obs.reference_range,
            "3.5 - 11"
        )
        self.assertEqual(
            obs.units,
            "g"
        )
        self.assertEqual(
            obs.observation_value,
            "123"
        )

    def test_update_from_api_dict_replaces_observation(self):
        lt = self.patient.lab_tests.create(**{
            "clinical_info":  'testing',
            "datetime_ordered": datetime.datetime(2015, 6, 17, 4, 15, 10),
            "lab_number": "11111",
            "site": u'^&        ^',
            "status": "Sucess",
            "test_code": "AN12",
            "test_name": "Anti-CV2 (CRMP-5) antibodies",
        })

        lt.observation_set.create(
            last_updated=datetime.datetime(2015, 6, 18, 4, 15, 10),
            observation_datetime=datetime.datetime(2015, 4, 15, 4, 15, 10),
            observation_number="12312",
            reference_range="3.5 - 11",
            units="g",
            observation_value="234"
        )

        lt.update_from_api_dict(self.patient, self.api_dict)

        obs = lt.observation_set.get()

        # this should have changed
        self.assertEqual(
            obs.observation_value,
            "123"
        )

        # the below stay the same
        self.assertEqual(
            obs.observation_name,
            "Aerobic bottle culture"
        )
        self.assertEqual(
            obs.observation_number,
            "12312"
        )
        self.assertEqual(
            obs.reference_range,
            "3.5 - 11"
        )
        self.assertEqual(
            obs.units,
            "g"
        )

    def test_extras(self):
        lt = self.patient.lab_tests.create(**{
            "clinical_info":  'testing',
            "datetime_ordered": datetime.datetime(2015, 6, 17, 4, 15, 10),
            "lab_number": "11111",
            "site": u'^&        ^',
            "status": "Sucess",
            "test_code": "AN12",
            "test_name": "Anti-CV2 (CRMP-5) antibodies",
        })

        lt.observation_set.create(
            last_updated=datetime.datetime(2015, 6, 18, 4, 15, 10),
            observation_datetime=datetime.datetime(2015, 4, 15, 4, 15, 10),
            observation_number="12312",
            reference_range="3.5 - 11",
            units="g",
            observation_value="234",
            observation_name="Aerobic bottle culture"
        )

        expected = {
            "clinical_info":  'testing',
            "lab_number": "11111",
            "site": u'^&        ^',
            "status": "Sucess",
            "test_code": "AN12",
            "test_name": "Anti-CV2 (CRMP-5) antibodies",
            "observations": [{
                "last_updated": '18/06/2015 04:15:10',
                "observation_datetime": '15/04/2015 04:15:10',
                "observation_name": "Aerobic bottle culture",
                "observation_number": "12312",
                "observation_value": "234",
                "reference_range": "3.5 - 11",
                "units": "g"
            }]
        }
        self.assertEqual(lt.extras, expected)

    def test_to_dict(self):
        lt = self.create_lab_test()
        result = lt.dict_for_view(None)
        expected = {
            'observations': [{
                'last_updated': '18/06/2015 04:15:10',
                'observation_value': '234',
                'units': 'g',
                'reference_range': '3.5 - 11',
                'observation_name': 'Aerobic bottle culture',
                'observation_datetime': '15/04/2015 04:15:10',
                'observation_number': '12312'
            }],
            'test_name': 'Anti-CV2 (CRMP-5) antibodies',
            'lab_number': '11111',
            'datetime_ordered': datetime.datetime(2015, 6, 17, 4, 15, 10),
            'test_code': 'AN12',
            'status': 'Sucess',
            'site': '^&        ^',
            'clinical_info': 'testing',
            'extras': {
                'observations': [{
                    'last_updated': '18/06/2015 04:15:10',
                    'observation_value': '234', 'units': 'g',
                    'reference_range': '3.5 - 11',
                    'observation_name': 'Aerobic bottle culture',
                    'observation_datetime': '15/04/2015 04:15:10',
                    'observation_number': '12312'
                }],
                'test_name': 'Anti-CV2 (CRMP-5) antibodies',
                'lab_number': '11111',
                'test_code': 'AN12',
                'status': 'Sucess',
                'site': '^&        ^',
                'clinical_info': 'testing'
            },
        }
        self.assertEqual(result, expected)

    def test_patient_deletion_behaviour(self):
        self.create_lab_test()
        self.patient.delete()
        self.assertFalse(
            models.LabTest.objects.all().exists()
        )

    def test_lab_test_deletion_behaviour(self):
        lt = self.create_lab_test()
        lt.delete()
        self.assertEqual(
            Patient.objects.get().id, self.patient.id
        )

    def test_observation_deletion_behaviour(self):
        lt = self.create_lab_test()
        obs = lt.observation_set.get()
        obs.delete()
        self.assertEqual(
            models.LabTest.objects.get().id,
            lt.id
        )


class ObservationTestCase(OpalTestCase):
    def test_value_numeric(self):
        patient, _ = self.new_patient_and_episode_please()
        observation = models.Observation()

        inputs_to_expected_results = (
            ("<1", float(1),),
            ("1>", float(1),),
            (" 1 ", float(1),),
            ("< 1", float(1),),
            (" < 1", float(1),),
            ("1 ~ some other things", float(1),),
            (".1 ", None),
            ("0.1 ", 0.1),
            ("1E", None),
            ("'1'", None),
        )
        for input_value, expected in inputs_to_expected_results:
            observation.observation_value = input_value
            self.assertEqual(observation.value_numeric, expected)