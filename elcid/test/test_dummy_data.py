"""
Unittests for elcid.data.dummy_api_data
"""
from opal.core.test import OpalTestCase

from elcid.data import dummy_api_data

class DataTestCase(OpalTestCase):

    def test_data_value(self):
        # Only really testing it imports without syntax errors TBH
        self.assertEqual(20334305, dummy_api_data.PATHOLOGY_DATA[0]['OBX_id'])
