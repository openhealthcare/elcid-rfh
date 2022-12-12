import copy
import datetime
from unittest.mock import patch
from opal.core.test import OpalTestCase
from plugins.admissions import loader
from plugins.admissions import models
from elcid import episode_categories


class CleanTransferHistoryRows(OpalTestCase):
    def setUp(self):
        self.now = datetime.datetime.now()
        created = self.now - datetime.timedelta(2)
        updated = self.now - datetime.timedelta(2)
        self.fake_row = {
            'TRANS_HIST_SEQ_NBR': 234,
            'SPELL_NUMBER': 345,
            'LOCAL_PATIENT_IDENTIFIER': 'ZZZ',
            'CREATED_DATE': created,
            'UPDATED_DATE': updated
        }

    def test_clean_transfer_history_rows_no_mrn(self):
        fake_row = copy.copy(self.fake_row)
        fake_row['LOCAL_PATIENT_IDENTIFIER'] = ' '
        result = list(loader.clean_transfer_history_rows([fake_row]))
        self.assertEqual(result, [])

    def test_clean_transfer_history_rows_dups(self):
        row_1 = copy.copy(self.fake_row)
        row_2 = copy.copy(self.fake_row)
        row_2['CREATED_DATE'] = self.now - datetime.timedelta(4)
        row_2['UPDATED_DATE'] = row_2['CREATED_DATE']
        result = list(loader.clean_transfer_history_rows([row_1, row_2]))
        self.assertEqual(result, [row_1])

    def test_clean_transfer_history_rows_no_dups(self):
        row_1 = copy.copy(self.fake_row)
        row_1['TRANS_HIST_SEQ_NBR'] = 123
        row_2 = copy.copy(self.fake_row)
        result = list(loader.clean_transfer_history_rows([row_1, row_2]))
        self.assertEqual(result, [row_1, row_2])


@patch('intrahospital_api.loader.create_rfh_patient_from_hospital_number')
@patch('plugins.admissions.loader.ProdAPI')
class LoadBedStatusTestCase(OpalTestCase):
    def setUp(self):
        self.bed_status_row = {
            i: None for i in models.BedStatus.UPSTREAM_FIELDS_TO_MODEL_FIELDS.keys()
        }

    def test_load_bed_status_new_patient(self, prod_api, create_rfh_patient_from_hospital_number):
        self.bed_status_row["Local_Patient_Identifier"] = "123"
        patient, _ = self.new_patient_and_episode_please()
        prod_api.return_value.execute_warehouse_query.return_value =[
            self.bed_status_row
        ]
        create_rfh_patient_from_hospital_number.return_value = patient
        loader.load_bed_status()
        bed_status = models.BedStatus.objects.get()
        create_rfh_patient_from_hospital_number.assert_called_once_with(
            "123", episode_categories.InfectionService
        )
        self.assertEqual(
            bed_status.patient, patient
        )

    def test_load_bed_status_existing_patient(self, prod_api, create_rfh_patient_from_hospital_number):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number= "123"
        )
        self.bed_status_row["Local_Patient_Identifier"] = "123"
        prod_api.return_value.execute_warehouse_query.return_value =[
            self.bed_status_row
        ]
        loader.load_bed_status()
        bed_status = models.BedStatus.objects.get()
        self.assertFalse(create_rfh_patient_from_hospital_number.called)
        self.assertEqual(
            bed_status.patient, patient
        )
