import copy
import datetime
from opal.core.test import OpalTestCase
from lab import models as lmodels
from intrahospital_api.apis.backends import lab_tests

FAKE_ROW_DATA = {
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
    u'Encounter_Consultant_Name': u'DR. M. BERELOWITZ',
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


MULTIPLE_RESULTS_LAB_TEST = [
    {
        u'OBR-5_Priority': u'Y',
        u'OBR_Sequence_ID': u'3',
        u'OBR_Status': u'F',
        u'OBR_exam_code_ID': u'M3',
        u'OBR_exam_code_Text': u'LIVER PROFILE',
        u'OBX_Sequence_ID': u'3',
        u'OBX_Status': u'F',
        u'OBX_exam_code_ID': u'AST',
        u'OBX_exam_code_Text': u'AST',
        u'OBX_id': 95454142,
        u'Observation_date': datetime.datetime(2018, 7, 20, 14, 1),
        u'Order_Number': u'',
        u'Relevant_Clinical_Info': u'urgent pre-chemo pancreas ca',
        u'Reported_date': datetime.datetime(2018, 7, 20, 14, 34),
        u'Request_Date': datetime.datetime(2018, 7, 20, 12, 28),
        u'Result_ID': u'74154192679',
        u'Result_Range': u'0 - 37',
        u'Result_Units': u'U/L',
        u'Result_Value': u'9',
        u'SEX': u'M',
        u'Specimen_Site': u'^&                              ^',
        u'Visit_Number': u'',
        u'crs_patient_masterfile_id': None,
        u'date_inserted': datetime.datetime(2018, 8, 27, 18, 57, 13, 480000),
        u'id': 27523621,
        u'last_updated': datetime.datetime(2018, 8, 27, 18, 57, 13, 480000),
        u'visible': u'Y'
    },
    {
        u'OBR-5_Priority': u'Y',
        u'OBR_Sequence_ID': u'5',
        u'OBR_Status': u'F',
        u'OBR_exam_code_ID': u'M12',
        u'OBR_exam_code_Text': u'UREA AND ELECTROLYTES',
        u'OBX_Sequence_ID': u'5',
        u'OBX_Status': u'F',
        u'OBX_exam_code_ID': u'MDRD',
        u'OBX_exam_code_Text': u'eGFR (MDRD)',
        u'OBX_id': 95454148,
        u'Observation_date': datetime.datetime(2018, 7, 20, 14, 1),
        u'Order_Number': u'',
        u'Relevant_Clinical_Info': u'urgent pre-chemo pancreas ca',
        u'Reported_date': datetime.datetime(2018, 7, 20, 14, 34),
        u'Request_Date': datetime.datetime(2018, 7, 20, 12, 28),
        u'Result_ID': u'74154192679',
        u'Result_Range': u'[               ]',
        u'Result_Units': u'mL/min',
        u'Result_Value': u'>90~ml/min/1.73 square metre~For Afro-Caribbean patients multiply eGFR by 1.21~For advice on interpretation of eGFR, refer to~NICE guidelines for CKD',
        u'SEX': u'M',
        u'Specimen_Site': u'^&                              ^',
        u'Visit_Number': u'',
        u'crs_patient_masterfile_id': None,
        u'date_inserted': datetime.datetime(2018, 8, 27, 18, 57, 13, 497000),
        u'id': 27523623,
        u'last_updated': datetime.datetime(2018, 8, 27, 18, 57, 13, 497000),
        u'visible': u'Y'
    }
]


class LabTestApiTestCase(OpalTestCase):
    maxDiff = None

    def get_row(self, **kwargs):
        raw_lab_tests = copy.copy(FAKE_ROW_DATA)
        raw_lab_tests.update(kwargs)
        return lab_tests.Row(raw_lab_tests)

    def test_demographics_dict(self):
        row = self.get_row()
        result = row.get_demographics_dict()

        expected = {
            'nhs_number': u'7060976728',
            'first_name': u'TEST',
            'surname': u'ZZZTEST',
            'title': '',
            'sex': 'Female',
            'hospital_number': u'20552710',
            'date_of_birth': '10/10/1980',
            'ethnicity': 'Mixed - White and Black Caribbean'
        }
        self.assertEqual(
            result, expected
        )

    def test_sex_male(self):
        row = self.get_row(
            CRS_SEX="M"
        )
        self.assertEqual(row.sex, "Male")

        row = self.get_row(
            CRS_SEX="",
            SEX="M"
        )

        self.assertEqual(row.sex, "Male")

    def test_sex_female(self):
        row = self.get_row(
            CRS_SEX="F"
        )
        self.assertEqual(row.sex, "Female")

        row = self.get_row(
            CRS_SEX="",
            SEX="F"
        )

    def test_ethnicity(self):
        row = self.get_row(
            CRS_Ethnic_Group="A"
        )
        self.assertEqual(row.ethnicity, "White - British")

    def test_date_of_birth(self):
        dt = datetime.datetime(2017, 10, 1)
        row = self.get_row(
            CRS_DOB=dt
        )
        self.assertEqual(row.date_of_birth, "01/10/2017")

        row = self.get_row(
            CRS_DOB="",
            date_of_birth=dt
        )

        self.assertEqual(row.date_of_birth, "01/10/2017")

    def test_status(self):
        row = self.get_row(OBX_Status="F")
        self.assertEqual(
            row.status, lmodels.LabTest.COMPLETE
        )

    def test_results_dict(self):
        row = self.get_row()
        result = row.get_results_dict()
        expected = {
            'clinical_info': u'testing',
            'datetime_ordered': '18/07/2015 16:18:00',
            'external_identifier': u'0013I245895',
            'last_updated': '18/07/2015 17:00:02',
            'observation_datetime': '18/07/2015 16:18:00',
            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
            'observation_number': 20334311,
            'status': 'complete',
            'observation_value': u'Negative',
            'test_code': u'ANNR',
            'test_name': u'ANTI NEURONAL AB REFERRAL',
            'units': u'',
            'reference_range': u' -',
            'site': u'^&                              ^',
        }
        self.assertEqual(result, expected)

    def test_cast_rows_to_lab_tests(self):
        api = lab_tests.LabTestApi()
        rows = [self.get_row()]
        result = api.cast_rows_to_lab_test(rows)
        self.assertEqual(
            result,
            [{
                'status': 'complete',
                'external_identifier': u'0013I245895',
                'external_system': 'RFH Database',
                'site': u'^&                              ^',
                'test_code': u'ANNR',
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
            }]
        )

    def test_cast_rows_to_lab_tests_multiple(self):
        api = lab_tests.LabTestApi()

        expected = [
            {
                'clinical_info': u'urgent pre-chemo pancreas ca',
                'datetime_ordered': '20/07/2018 14:01:00',
                'external_identifier': u'74154192679',
                'external_system': 'RFH Database',
                'observations': [{
                    'last_updated': '27/08/2018 18:57:13',
                    'observation_datetime': '20/07/2018 14:01:00',
                    'observation_name': u'AST',
                    'observation_number': 95454142,
                    'observation_value': u'9',
                    'reference_range': u'0 - 37',
                    'units': u'U/L'
                  }],
                'site': u'^&                              ^',
                'status': 'complete',
                'test_code': u'M3',
                'test_name': u'LIVER PROFILE'
            },
            {
                'clinical_info': u'urgent pre-chemo pancreas ca',
                'datetime_ordered': '20/07/2018 14:01:00',
                'external_identifier': u'74154192679',
                'external_system': 'RFH Database',
                'observations': [{
                    'last_updated': '27/08/2018 18:57:13',
                    'observation_datetime': '20/07/2018 14:01:00',
                    'observation_name': u'eGFR (MDRD)',
                    'observation_number': 95454148,
                    'observation_value': u'>90~ml/min/1.73 square metre~For Afro-Caribbean patients multiply eGFR by 1.21~For advice on interpretation of eGFR, refer to~NICE guidelines for CKD',
                    'reference_range': u'[               ]',
                    'units': u'mL/min'
                }],
                'site': u'^&                              ^',
                'status': 'complete',
                'test_code': u'M12',
                'test_name': u'UREA AND ELECTROLYTES'
            }]

        row_1 = self.get_row(**MULTIPLE_RESULTS_LAB_TEST[0])
        row_2 = self.get_row(**MULTIPLE_RESULTS_LAB_TEST[1])
        rows = [row_1, row_2]
        result = api.cast_rows_to_lab_test(rows)
        self.assertEqual(
            result, expected
        )

    def test_all_fields(self):
        row = self.get_row()
        result = row.get_all_fields()
        expected = {
            'external_identifier': u'0013I245895',
            'nhs_number': u'7060976728',
            'first_name': u'TEST',
            'surname': u'ZZZTEST',
            'title': '',
            'sex': 'Female',
            'hospital_number': u'20552710',
            'date_of_birth': '10/10/1980',
            'ethnicity': 'Mixed - White and Black Caribbean',
            'clinical_info': u'testing',
            'datetime_ordered': '18/07/2015 16:18:00',
            'last_updated': '18/07/2015 17:00:02',
            'observation_datetime': '18/07/2015 16:18:00',
            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
            'observation_number': 20334311,
            'observation_value': u'Negative',
            'reference_range': u' -',
            'site': u'^&                              ^',
            'status': 'complete',
            'test_code': u'ANNR',
            'test_name': u'ANTI NEURONAL AB REFERRAL',
            'units': u''
        }
        self.assertEqual(result, expected)
