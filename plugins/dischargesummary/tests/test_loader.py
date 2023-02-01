from unittest.mock import patch
from opal.core.test import OpalTestCase
from plugins.dischargesummary import loader


@patch('plugins.dischargesummary.loader.ProdAPI')
class QueryForZeroPrefixedTestCase(OpalTestCase):
    def test_query_found_zero_prefixed(self, prod_api):
        prod_api.return_value.execute_hospital_query.return_value = [
            {"RF1_NUMBER": "00123"}
        ]
        result = loader.query_for_zero_prefixed('123')
        self.assertEqual(result, ['00123'])

    def test_flawed_zero_prefixed(self, prod_api):
        prod_api.return_value.execute_hospital_query.return_value = [
            {"RF1_NUMBER": "100123"}
        ]
        result = loader.query_for_zero_prefixed('123')
        self.assertEqual(result, [])


@patch('plugins.dischargesummary.loader.query_for_zero_prefixed')
class GetMRNsToQueryForPatient(OpalTestCase):
    def test_gets_zero_prefixed_active_and_inactive_mrns(self, query_for_zero_prefixed):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        patient.mergedmrn_set.create(
            mrn="234"
        )
        zero_prefixed_results = {
            "123": [],
            "234": ["00234"]
        }
        query_for_zero_prefixed.side_effect = lambda x: zero_prefixed_results[x]
        result = loader.get_mrns_to_query_for_patient(patient)
        self.assertEqual(
            ["123", "234", "00234"], result
        )
