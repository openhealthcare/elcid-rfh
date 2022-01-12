import copy
import datetime
from opal.core.test import OpalTestCase
from plugins.admissions import loader


class CleanTransferHistoryRows(OpalTestCase):
    def setUp(self):
        self.now = datetime.datetime.now()
        created = self.now - datetime.timedelta(2)
        updated = self.now - datetime.timedelta(2)
        self.fake_row = {
            'TRANS_HIST_SEQ_NBR': 234,
            'SPELL_NUMBER': 345,
            'LOCAL_PATIENT_IDENTIFIER': 'ZZZ',
            'created_datetime': created,
            'updated_datetime': updated
        }

    def test_clean_transfer_history_rows_no_mrn(self):
        fake_row = copy.copy(self.fake_row)
        fake_row['LOCAL_PATIENT_IDENTIFIER'] = ' '
        result = list(loader.clean_transfer_history_rows([fake_row]))
        self.assertEqual(result, [])

    def test_clean_transfer_history_rows_dups(self):
        row_1 = copy.copy(self.fake_row)
        row_2 = copy.copy(self.fake_row)
        row_2['created_datetime'] = self.now - datetime.timedelta(4)
        result = list(loader.clean_transfer_history_rows([row_1, row_2]))
        self.assertEqual(result, [row_1])

    def test_clean_transfer_history_rows_no_dups(self):
        row_1 = copy.copy(self.fake_row)
        row_1['TRANS_HIST_SEQ_NBR'] = 123
        row_2 = copy.copy(self.fake_row)
        result = list(loader.clean_transfer_history_rows([row_1, row_2]))
        self.assertEqual(result, [row_1, row_2])
