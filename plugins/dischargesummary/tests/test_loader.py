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
