import copy
import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from plugins.admissions import loader, models




class TansferHistoriesTestCase(OpalTestCase):
    def test_create_transfer_histories(self):
        """
        Tests that the create transfer histories loader
        populates the key fields on the model
        """
        row = {
            k: None for k in models.TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS.keys()
        }

        two_days_ago = datetime.datetime.now() - datetime.timedelta(2)
        yesterday = datetime.datetime.now() - datetime.timedelta(1)

        row["ENCNTR_SLICE_ID"] = 1231231
        row["LOCAL_PATIENT_IDENTIFIER"] = "123"
        row["SITE_CODE"] = "1231231"
        row["ENCNTR_SLICE_ID"] = 1231231
        row["UNIT"] = "X"
        row["ROOM"] = "7W"
        row["BED"] = "B12"
        row["In_TransHist"] = 1
        row["In_Spells"] = 1
        row["TRANS_HIST_START_DT_TM"] = two_days_ago
        row["TRANS_HIST_END_DT_TM"] = yesterday


        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        loader.create_transfer_histories([row])
        found_th = patient.transferhistory_set.get()
        self.assertEqual(found_th.encounter_slice_id, row["ENCNTR_SLICE_ID"])
        self.assertEqual(found_th.site_code, row["SITE_CODE"])
        self.assertEqual(found_th.unit, row["UNIT"])
        self.assertEqual(found_th.room, row["ROOM"])
        self.assertEqual(found_th.bed, row["BED"])
        self.assertEqual(
            found_th.transfer_start_datetime.date(), datetime.date.today() - datetime.timedelta(2)
        )
        self.assertEqual(
            found_th.transfer_end_datetime.date(), datetime.date.today() - datetime.timedelta(1)
        )
