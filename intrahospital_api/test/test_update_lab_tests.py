import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api import update_lab_tests
from plugins.labtests import models as lab_test_models


class TestGetOrCreateLabTest(OpalTestCase):
    def setUp(self):
        self.api_dict = {
            "clinical_info":  'testing',
            "datetime_ordered": "17/07/2015 04:15:10",
            "external_identifier": "11111",
            "site": u'some site',
            "status": "Success",
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

    def test_creates_lab_test(self):
        lt = update_lab_tests.delete_and_create_lab_test(
            self.patient, self.api_dict
        )

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
            lt.status, 'Success'
        )
        self.assertEqual(
            lt.test_code, 'AN12'
        )
        self.assertEqual(
            lt.test_name, 'Anti-CV2 (CRMP-5) antibodies'
        )

        self.assertEqual(
            lt.site, 'some site'
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

        self.assertEqual(
            lab_test_models.LabTest.objects.all().count(), 1
        )

    def test_replaces_lab_test(self):
        lab_test_models.LabTest.objects.create(**{
            "patient": self.patient,
            "clinical_info":  'testing',
            "datetime_ordered": timezone.make_aware(datetime.datetime(
                2015, 7, 17, 4, 15, 10
            )),
            "lab_number": "11111",
            "site": 'some site',
            "status": "Pending",
            "test_code": "AN12",
            "test_name": "Anti-CV2 (CRMP-5) antibodies",
        })

        lt = update_lab_tests.delete_and_create_lab_test(
            self.patient, self.api_dict
        )
        self.assertEqual(lt.status, "Success")
        # check the model did actually save
        self.assertEqual(
            lab_test_models.LabTest.objects.get().status,
            "Success"
        )
