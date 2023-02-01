from unittest import mock
from plugins.labtests import models as lab_models
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import load_all_lab_tests
import datetime

FAKE_PATHOLOGY_DATA = {
    u'Abnormal_Flag': u'',
    u'Accession_number': u'73151060487',
    u'CRS_ADDRESS_LINE1': u'James Centre',
    u'CRS_ADDRESS_LINE2': u'39 Winston Terrace',
    u'CRS_ADDRESS_LINE3': u'LONDON',
    u'CRS_ADDRESS_LINE4': u'',
    u'CRS_DOB': datetime.datetime(1980, 10, 10, 0, 0),
    u'CRS_Date_of_Death': datetime.datetime(1900, 1, 1, 0, 0),
    u'CRS_Deceased_Flag': u'ALIVE',
    u'CRS_EMAIL': u'',
    u'CRS_Ethnic_Group': u'D',
    u'CRS_Forename1': u'TEST',
    u'CRS_Forename2': u'',
    u'CRS_GP_NATIONAL_CODE': u'G1004756',
    u'CRS_GP_PRACTICE_CODE': u'H84012',
    u'CRS_HOME_TELEPHONE': u'0111111111',
    u'CRS_MAIN_LANGUAGE': u'',
    u'CRS_MARITAL_STATUS': u'',
    u'CRS_MOBILE_TELEPHONE': u'',
    u'CRS_NATIONALITY': u'GBR',
    u'CRS_NHS_Number': u'',
    u'CRS_NOK_ADDRESS1': u'',
    u'CRS_NOK_ADDRESS2': u'',
    u'CRS_NOK_ADDRESS3': u'',
    u'CRS_NOK_ADDRESS4': u'',
    u'CRS_NOK_FORENAME1': u'',
    u'CRS_NOK_FORENAME2': u'',
    u'CRS_NOK_HOME_TELEPHONE': u'',
    u'CRS_NOK_MOBILE_TELEPHONE': u'',
    u'CRS_NOK_POST_CODE': u'',
    u'CRS_NOK_RELATIONSHIP': u'',
    u'CRS_NOK_SURNAME': u'',
    u'CRS_NOK_TYPE': u'',
    u'CRS_NOK_WORK_TELEPHONE': u'',
    u'CRS_Postcode': u'N6 P12',
    u'CRS_Religion': u'',
    u'CRS_SEX': u'F',
    u'CRS_Surname': u'ZZZTEST',
    u'CRS_Title': u'',
    u'CRS_WORK_TELEPHONE': u'',
    u'DOB': datetime.datetime(1964, 1, 1, 0, 0),
    u'Date_Last_Obs_Normal': datetime.datetime(2015, 7, 18, 16, 26),
    u'Date_of_the_Observation': datetime.datetime(2015, 7, 18, 16, 26),
    u'Department': u'9',
    u'Encounter_Consultant_Code': u'C2754019',
    u'Encounter_Consultant_Name': u'DR. M. SMITH',
    u'Encounter_Consultant_Type': u'',
    u'Encounter_Location_Code': u'6N',
    u'Encounter_Location_Name': u'RAL 6 NORTH',
    u'Encounter_Location_Type': u'IP',
    u'Event_Date': datetime.datetime(2015, 7, 18, 16, 47),
    u'Firstname': u'TEST',
    u'MSH_Control_ID': u'18498139',
    u'OBR-5_Priority': u'N',
    u'OBR_Sequence_ID': u'2',
    u'OBR_Status': u'F',
    u'OBR_exam_code_ID': u'ANNR',
    u'OBR_exam_code_Text': u'ANTI NEURONAL AB REFERRAL',
    u'OBX_Sequence_ID': u'11',
    u'OBX_Status': u'F',
    u'OBX_exam_code_ID': u'AN12',
    u'OBX_exam_code_Text': u'Anti-CV2 (CRMP-5) antibodies',
    u'OBX_id': 20334311,
    u'ORC-9_Datetime_of_Transaction': datetime.datetime(2015, 7, 18, 16, 47),
    u'Observation_date': datetime.datetime(2015, 7, 18, 16, 18),
    u'Order_Number': u'',
    u'Patient_Class': u'NHS',
    u'Patient_ID_External': u'7060976728',
    u'Patient_Number': u'20552710',
    u'Relevant_Clinical_Info': u'testing',
    u'Reported_date': datetime.datetime(2015, 7, 18, 16, 26),
    u'Request_Date': datetime.datetime(2015, 7, 18, 16, 15),
    u'Requesting_Clinician': u'C4369059_Chee Ronnie',
    u'Result_ID': u'0013I245895',
    u'Result_Range': u' -',
    u'Result_Units': u'',
    u'Result_Value': u'Negative',
    u'SEX': u'F',
    u'Specimen_Site': u'^&                              ^',
    u'Surname': u'ZZZTEST',
    u'Visit_Number': u'',
    u'crs_patient_masterfile_id': None,
    u'date_inserted': datetime.datetime(2015, 7, 18, 17, 0, 2, 240000),
    u'id': 5949264,
    u'last_updated': datetime.datetime(2015, 7, 18, 17, 0, 2, 240000),
    u'visible': u'Y'
}


class GetAllHospitalNumbersTestCase(OpalTestCase):
    def test_get_all_hospital_numbers(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        patient.mergedmrn_set.create(
            mrn='234'
        )
        self.assertEqual(
            load_all_lab_tests.get_all_hospital_numbers(),
            set(["123", "234"])
        )


class CastToLabTestDictTestCase(OpalTestCase):
    @mock.patch(
        'intrahospital_api.management.commands.load_all_lab_tests.timezone.now'
    )
    def test_cast_to_lab_test_dict(self, now_value):
        now = timezone.make_aware(
            datetime.datetime(2023, 1, 30, 13, 00)
        )
        now_value.return_value = now
        result = load_all_lab_tests.cast_to_lab_test_dict(FAKE_PATHOLOGY_DATA, 1)
        self.assertEqual(
            result["patient_id"], 1
        )
        mappings = {
            "clinical_info": "Relevant_Clinical_Info",
            "datetime_ordered": "Observation_date",
            "lab_number": "Result_ID",
            "test_code": "OBR_exam_code_ID",
            "test_name": "OBR_exam_code_Text",
            "encounter_consultant_name": "Encounter_Consultant_Name",
            "encounter_location_code": "Encounter_Location_Code",
            "encounter_location_name": "Encounter_Location_Name",
            "accession_number": "Accession_number",
        }
        for our_key, their_key in mappings.items():
            self.assertEqual(
                result[our_key], FAKE_PATHOLOGY_DATA[their_key]
            )
        self.assertEqual(
            result["created_at"], now
        )
        self.assertEqual(
            result["updated_at"], now
        )
        self.assertEqual(result["department_int"], 9)
        self.assertEqual(result["status"], 'complete')
        self.assertEqual(result["site"], "^&                              ^")
        patient, _ = self.new_patient_and_episode_please()
        result["patient_id"] = patient.id
        # Sanity check in case we have changed the fields on the model
        lab_models.LabTest.objects.create(
            **result
        )

    @mock.patch(
        'intrahospital_api.management.commands.load_all_lab_tests.timezone.now'
    )
    def test_cast_to_observation_dict(self, now_value):
        now = timezone.make_aware(
            datetime.datetime(2023, 1, 30, 13, 00)
        )
        now_value.return_value = now
        result = load_all_lab_tests.cast_to_observation_dict(FAKE_PATHOLOGY_DATA, 1)
        self.assertEqual(result["test_id"], 1)
        mappings = {
            "last_updated": "last_updated",
            "observation_datetime": "Observation_date",
            "reported_datetime": "Reported_date",
            "reference_range": "Result_Range",
            "observation_number": "OBX_id",
            "observation_name": "OBX_exam_code_Text",
            "observation_value": "Result_Value",
            "units": "Result_Units",
        }
        for our_key, their_key in mappings.items():
            self.assertEqual(
                result[our_key], FAKE_PATHOLOGY_DATA[their_key]
            )
        patient, _ = self.new_patient_and_episode_please()
        lab_test = patient.lab_tests.create()
        result['test_id'] = lab_test.id
        lab_models.Observation.objects.create(
            **result
        )
