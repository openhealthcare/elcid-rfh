import mock
import datetime
import copy
from django.utils import timezone
from django.test import override_settings
from intrahospital_api.test.test_loader import ApiTestCase
from intrahospital_api import deployment_check
from elcid import models as elcid_models

UPDATE_DICT = {
    'status': 'complete',
    'external_identifier': u'0013I245895',
    'external_system': 'RFH Database',
    'site': u'^&                              ^',
    'test_code': u'ANNR',
    'lab_test_type': elcid_models.UpstreamLabTest.get_display_name(),
    'test_name': u'ANTI NEURONAL AB REFERRAL',
    'clinical_info': u'testing',
    'datetime_ordered': '18/07/2015 16:18:00',
    'observations': [{
        'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
        'observation_number': 20334311,
        'observation_value': u'Negative',
        'observation_datetime': '18/07/2015 16:18:00',
        'units': u'', 'last_updated': '18/07/2015 17:00:02',
        'reference_range': u' -'
    }]
}


class DeploymentCheckTestCase(ApiTestCase):
    def setUp(self):
        super(DeploymentCheckTestCase, self).setUp()
        self.patient, _ = self.new_patient_and_episode_please()

    def create_lab_test(self, **kwargs):
        update_dict = copy.copy(UPDATE_DICT)
        update_dict.update(**kwargs)
        upstream_test = elcid_models.UpstreamLabTest()
        upstream_test = upstream_test.update_from_api_dict(
            self.patient, update_dict, self.user
        )
        return 1

    @override_settings(OPAL_BRAND_NAME="prods")
    def test_does_not_run_if_not_test_in_name(self):
        result = {}
        some_dt = timezone.make_aware(datetime.datetime(2014, 1 ,1))

        with self.assertRaises(ValueError):
            deployment_check.check_since(some_dt, result)



    @mock.patch("intrahospital_api.deployment_check.service.update_patients")
    @mock.patch("intrahospital_api.deployment_check.service.update_patient")
    @override_settings(OPAL_BRAND_NAME="unit_test")
    def test_results(self, update_patient, update_patients):
        result = {}
        # has to be below the observation datetime
        some_dt = timezone.make_aware(datetime.datetime(2014, 1 ,1))
        self.create_lab_test()

        def batch_load(*args, **kwargs):
            self.create_lab_test()
            self.create_lab_test()
            return 2

        def initial_load(*args, **kwargs):
            self.create_lab_test()
            self.create_lab_test()
            self.create_lab_test()
            return 3

        update_patients.side_effect = batch_load
        update_patient.side_effect = initial_load
        with self.assertRaises(deployment_check.RollBackError):
            deployment_check.check_since(some_dt, result)

        self.assertEqual(
            result["current"], 1
        )

        self.assertEqual(
            result["batch_load"], 2
        )

        self.assertEqual(
            result["initial_load"], 3
        )

        # make sure the roll back has happened
        self.assertEqual(
            self.patient.labtest_set.count(), 1
        )




