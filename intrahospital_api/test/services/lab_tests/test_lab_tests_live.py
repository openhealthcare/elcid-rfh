import copy
import mock
import datetime
from opal.core.test import OpalTestCase
from lab import models as lmodels
from intrahospital_api.services.lab_tests.backends import live

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


class BaseLabTestCase(OpalTestCase):
    def get_row(self, **kwargs):
        raw_lab_tests = copy.copy(FAKE_ROW_DATA)
        raw_lab_tests.update(kwargs)
        return live.Row(raw_lab_tests)


class RowTestCase(BaseLabTestCase):
    maxDiff = None

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

    def test_all_fields(self):
        row = self.get_row()
        result = row.get_all_fields()
        expected = {
            'external_identifier': u'0013I245895',
            'hospital_number': u'20552710',
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


class LabTestApiTestCase(BaseLabTestCase):
    @mock.patch(
        "intrahospital_api.services.lab_tests.backends.live.Api.data_delta_query"
    )
    def test_lab_test_results_since_no_hospital_number(self, ddq):
        api = live.Api()
        ddq.return_value = (i for i in [self.get_row()])
        result = api.lab_test_results_since([], datetime.datetime.now())
        self.assertEqual(list(result), [])

    @mock.patch(
        "intrahospital_api.services.lab_tests.backends.live.Api.data_delta_query"
    )
    def test_lab_test_results_since_hospital_number(self, ddq):
        api = live.Api()
        ddq.return_value = (i for i in [self.get_row()])
        result = api.lab_test_results_since(['20552710'], datetime.datetime.now())
        expected = [{
            'status': 'complete', 
            'external_identifier': u'0013I245895', 
            'site': u'^&                              ^', 
            'test_code': u'ANNR', 
            'observations': [{
                'observation_name': u'Anti-CV2 (CRMP-5) antibodies', 
                'observation_number': 20334311, 
                'observation_value': u'Negative', 
                'observation_datetime': '18/07/2015 16:18:00',
                'units': u'',
                'last_updated': '18/07/2015 17:00:02', 
                'reference_range': u' -'}], 
            'test_name': u'ANTI NEURONAL AB REFERRAL', 
            'clinical_info': u'testing', 
            'external_system': 'RFH Database', 
            'datetime_ordered': '18/07/2015 16:18:00'
        }]
        self.assertEqual(result['20552710'], expected)

    def test_cast_rows_to_lab_tests(self):
        api = live.Api()
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
        api = live.Api()
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

    def test_data_deltas(self):
        self.maxDiff = None
        api = live.Api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )
        expected_result = {
            '20552710': [{
                'status': 'complete',
                'external_identifier': u'0013I245895',
                'site': u'^&                              ^',
                'test_code': u'ANNR',
                'observations': [
                    {
                        'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                        'observation_number': 20334311,
                        'observation_value': u'Negative',
                        'observation_datetime': '18/07/2015 16:18:00',
                        'units': u'',
                        'last_updated': '18/07/2015 17:00:02',
                        'reference_range': u' -'
                    }
                ],
                'test_name': u'ANTI NEURONAL AB REFERRAL',
                'clinical_info': u'testing',
                'external_system': 'RFH Database',
                'datetime_ordered': '18/07/2015 16:18:00'
            }]
        }
        with mock.patch.object(api, "data_delta_query") as execute_query:
            expected = [self.get_row()]
            execute_query.return_value = expected
            since = datetime.datetime.now()
            result = api.lab_test_results_since(['20552710'], since)
        self.assertEqual(
            result, expected_result
        )

    def test_data_deltas_none(self):
        """
        If the db query does not return anything
        we should return an empty iterator
        """

        api = live.Api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            expected = []
            execute_query.return_value = expected
            since = datetime.datetime.now()
            result = api.lab_test_results_since(['20552711'], since)
        self.assertEqual(
            result, {}
        )

    def test_data_deltas_no_patient(self):
        """
        If the db query return something but we have
        no patients, we should return an empty
        list
        """
        api = live.Api()
        with mock.patch.object(api, "data_delta_query") as execute_query:
            expected = [self.get_row()]
            execute_query.return_value = expected
            since = datetime.datetime.now()
            result = api.lab_test_results_since([], since)
        self.assertEqual(
            result, {}
        )

    def test_data_deltas_multiple_tests(self):
        """
        If there are multiple tests for a patient
        we should see this in the output
        """
        self.maxDiff = None
        expected = [
            self.get_row(Result_ID="122"),
            self.get_row(Result_ID="123")
        ]
        expected_result = {
            '20552710': [
                {
                    'status': 'complete',
                    'external_identifier': u'122',
                    'site': u'^&                              ^',
                    'test_code': u'ANNR',
                    'observations': [
                        {
                            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                            'observation_number': 20334311,
                            'observation_value': u'Negative',
                            'observation_datetime': '18/07/2015 16:18:00',
                            'units': u'',
                            'last_updated': '18/07/2015 17:00:02',
                            'reference_range': u' -'
                        }
                    ],
                    'test_name': u'ANTI NEURONAL AB REFERRAL',
                    'clinical_info': u'testing',
                    'external_system': 'RFH Database',
                    'datetime_ordered': '18/07/2015 16:18:00'
                },
                {
                    'status': 'complete',
                    'external_identifier': u'123',
                    'site': u'^&                              ^',
                    'test_code': u'ANNR',
                    'observations': [
                        {
                            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                            'observation_number': 20334311,
                            'observation_value': u'Negative',
                            'observation_datetime': '18/07/2015 16:18:00',
                            'units': u'',
                            'last_updated': '18/07/2015 17:00:02',
                            'reference_range': u' -'
                        }
                    ],
                    'test_name': u'ANTI NEURONAL AB REFERRAL',
                    'clinical_info': u'testing',
                    'external_system': 'RFH Database',
                    'datetime_ordered': '18/07/2015 16:18:00'
                },
            ]
        }

        api = live.Api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            execute_query.return_value = expected
            since = datetime.datetime.now()
            result = api.lab_test_results_since(["20552710"], since)
        self.assertEqual(
            result, expected_result
        )

    def test_data_deltas_same_test_number_different_test_type(self):
        """
        A patient can have multiple lab tests with the same
        number but with different types.

        We should see these as seperate tests in the output.
        """
        expected = [
            self.get_row(Result_ID="122", OBR_exam_code_Text="Blood"),
            self.get_row(Result_ID="122", OBR_exam_code_Text="Commentry")
        ]
        expected_result = {
            '20552710': [
                {
                    'status': 'complete',
                    'external_identifier': u'122',
                    'site': u'^&                              ^',
                    'test_code': u'ANNR',
                    'observations': [
                        {
                            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                            'observation_number': 20334311,
                            'observation_value': u'Negative',
                            'observation_datetime': '18/07/2015 16:18:00',
                            'units': u'',
                            'last_updated': '18/07/2015 17:00:02',
                            'reference_range': u' -'
                        }
                    ],
                    'test_name': u'Blood',
                    'clinical_info': u'testing',
                    'external_system': 'RFH Database',
                    'datetime_ordered': '18/07/2015 16:18:00'
                },
                {
                    'status': 'complete',
                    'external_identifier': u'122',
                    'site': u'^&                              ^',
                    'test_code': u'ANNR',
                    'observations': [
                        {
                            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                            'observation_number': 20334311,
                            'observation_value': u'Negative',
                            'observation_datetime': '18/07/2015 16:18:00',
                            'units': u'',
                            'last_updated': '18/07/2015 17:00:02',
                            'reference_range': u' -'
                        }
                    ],
                    'test_name': u'Commentry',
                    'clinical_info': u'testing',
                    'external_system': 'RFH Database',
                    'datetime_ordered': '18/07/2015 16:18:00'
                },
            ]
        }

        api = live.Api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            execute_query.return_value = expected
            since = datetime.datetime.now()
            result = api.lab_test_results_since(["20552710"], since)
        self.assertEqual(
            result, expected_result
        )

    def test_data_deltas_multiple_observations(self):
        """
        Multiple observations with the same lab test
        number should be aggregated
        """
        self.maxDiff = None
        expected = [
            self.get_row(Result_ID="122", OBX_id=20334311),
            self.get_row(Result_ID="122", OBX_id=20334312)
        ]
        expected_result = {
            '20552710': [
                {
                    'status': 'complete',
                    'external_identifier': u'122',
                    'site': u'^&                              ^',
                    'test_code': u'ANNR',
                    'observations': [
                        {
                            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                            'observation_number': 20334311,
                            'observation_value': u'Negative',
                            'observation_datetime': '18/07/2015 16:18:00',
                            'units': u'',
                            'last_updated': '18/07/2015 17:00:02',
                            'reference_range': u' -'
                        },
                        {
                            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                            'observation_number': 20334312,
                            'observation_value': u'Negative',
                            'observation_datetime': '18/07/2015 16:18:00',
                            'units': u'',
                            'last_updated': '18/07/2015 17:00:02',
                            'reference_range': u' -'
                        }
                    ],
                    'test_name': u'ANTI NEURONAL AB REFERRAL',
                    'clinical_info': u'testing',
                    'external_system': 'RFH Database',
                    'datetime_ordered': '18/07/2015 16:18:00'
                },
            ]
        }

        api = live.Api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            execute_query.return_value = expected
            since = datetime.datetime.now()
            result = api.lab_test_results_since(["20552710"], since)
        self.assertEqual(
            result, expected_result
        )

    def test_data_deltas_multiple_patients(self):
        """
        Multiple patients with lab tests
        """
        expected = [
            self.get_row(Patient_Number="123", Result_ID="124"),
            self.get_row(Patient_Number="125", Result_ID="126"),
        ]
        expected_result = {
            '123': [{
                    'status': 'complete',
                    'external_identifier': u'124',
                    'site': u'^&                              ^',
                    'test_code': u'ANNR',
                    'observations': [
                        {
                            'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                            'observation_number': 20334311,
                            'observation_value': u'Negative',
                            'observation_datetime': '18/07/2015 16:18:00',
                            'units': u'',
                            'last_updated': '18/07/2015 17:00:02',
                            'reference_range': u' -'
                        }
                    ],
                    'test_name': u'ANTI NEURONAL AB REFERRAL',
                    'clinical_info': u'testing',
                    'external_system': 'RFH Database',
                    'datetime_ordered': '18/07/2015 16:18:00'
            }],
            "125": [{
                        'status': 'complete',
                        'external_identifier': u'126',
                        'site': u'^&                              ^',
                        'test_code': u'ANNR',
                        'observations': [
                            {
                                'observation_name': u'Anti-CV2 (CRMP-5) antibodies',
                                'observation_number': 20334311,
                                'observation_value': u'Negative',
                                'observation_datetime': '18/07/2015 16:18:00',
                                'units': u'',
                                'last_updated': '18/07/2015 17:00:02',
                                'reference_range': u' -'
                            }
                        ],
                        'test_name': u'ANTI NEURONAL AB REFERRAL',
                        'clinical_info': u'testing',
                        'external_system': 'RFH Database',
                        'datetime_ordered': '18/07/2015 16:18:00'
            }]
        }

        api = live.Api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='123'
        )

        patient_2, _ = self.new_patient_and_episode_please()
        patient_2.demographics_set.update(
            hospital_number='125'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            execute_query.return_value = expected
            since = datetime.datetime.now()
            result = api.lab_test_results_since(["123", "125"], since)
        self.assertEqual(
            result, expected_result
        )
