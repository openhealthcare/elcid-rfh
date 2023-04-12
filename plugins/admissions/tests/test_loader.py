import datetime
from opal.core.test import OpalTestCase
from django.utils import timezone
from plugins.admissions import loader, models
from unittest.mock import patch
from elcid import episode_categories


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

    def test_load_bed_status_does_not_create_patients_with_empty_mrns(self, prod_api, create_rfh_patient_from_hospital_number):
        self.bed_status_row["Local_Patient_Identifier"] = ""
        prod_api.return_value.execute_warehouse_query.return_value =[
            self.bed_status_row
        ]
        loader.load_bed_status()
        self.assertFalse(
            create_rfh_patient_from_hospital_number.called
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

    def test_bed_status_can_have_none_patient(self, prod_api, create_rfh_patient_from_hospital_number):
        self.bed_status_row["Local_Patient_Identifier"] = None
        prod_api.return_value.execute_warehouse_query.return_value =[
            self.bed_status_row
        ]
        loader.load_bed_status()
        bed_status = models.BedStatus.objects.get()
        self.assertIsNone(bed_status.patient)


@patch('intrahospital_api.loader.create_rfh_patient_from_hospital_number')
@patch('plugins.admissions.loader.ProdAPI')
class LoadEncountersSinceTestCase(OpalTestCase):
    def setUp(self):
        self.encounter_row = {
            i: None for i in models.Encounter.UPSTREAM_FIELDS_TO_MODEL_FIELDS.keys()
        }

    def test_load_encounters_since_new_patient(self, prod_api, create_rfh_patient_from_hospital_number):
        self.encounter_row["PID_3_MRN"] = "123"
        patient, _ = self.new_patient_and_episode_please()
        prod_api.return_value.execute_hospital_query.return_value =[
            self.encounter_row
        ]
        create_rfh_patient_from_hospital_number.return_value = patient
        loader.load_excounters_since(timezone.now())
        encounter = models.Encounter.objects.get()
        create_rfh_patient_from_hospital_number.assert_called_once_with(
            "123", episode_categories.InfectionService
        )
        self.assertEqual(
            encounter.patient, patient
        )

    def test_load_encounters_existing_patient(self, prod_api, create_rfh_patient_from_hospital_number):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number= "123"
        )
        self.encounter_row["PID_3_MRN"] = "123"
        prod_api.return_value.execute_hospital_query.return_value =[
            self.encounter_row
        ]
        loader.load_excounters_since(timezone.now())
        bed_status = models.Encounter.objects.get()
        self.assertFalse(create_rfh_patient_from_hospital_number.called)
        self.assertEqual(
            bed_status.patient, patient
        )
