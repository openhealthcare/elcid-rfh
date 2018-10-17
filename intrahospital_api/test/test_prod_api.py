import mock
import copy
from django.test import override_settings
from pytds.tds import OperationalError
from datetime import datetime, date
from opal.core.test import OpalTestCase
from intrahospital_api.apis import prod_api
from intrahospital_api import constants
from lab import models as lmodels


FAKE_PATHOLOGY_DATA = {
    u'Abnormal_Flag': u'',
    u'Accession_number': u'73151060487',
    u'CRS_ADDRESS_LINE1': u'James Centre',
    u'CRS_ADDRESS_LINE2': u'39 Winston Terrace',
    u'CRS_ADDRESS_LINE3': u'LONDON',
    u'CRS_ADDRESS_LINE4': u'',
    u'CRS_DOB': datetime(1980, 10, 10, 0, 0),
    u'CRS_Date_of_Death': datetime(1900, 1, 1, 0, 0),
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
    u'DOB': datetime(1964, 1, 1, 0, 0),
    u'Date_Last_Obs_Normal': datetime(2015, 7, 18, 16, 26),
    u'Date_of_the_Observation': datetime(2015, 7, 18, 16, 26),
    u'Department': u'9',
    u'Encounter_Consultant_Code': u'C2754019',
    u'Encounter_Consultant_Name': u'DR. M. BERELOWITZ',
    u'Encounter_Consultant_Type': u'',
    u'Encounter_Location_Code': u'6N',
    u'Encounter_Location_Name': u'RAL 6 NORTH',
    u'Encounter_Location_Type': u'IP',
    u'Event_Date': datetime(2015, 7, 18, 16, 47),
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
    u'ORC-9_Datetime_of_Transaction': datetime(2015, 7, 18, 16, 47),
    u'Observation_date': datetime(2015, 7, 18, 16, 18),
    u'Order_Number': u'',
    u'Patient_Class': u'NHS',
    u'Patient_ID_External': u'7060976728',
    u'Patient_Number': u'20552710',
    u'Relevant_Clinical_Info': u'testing',
    u'Reported_date': datetime(2015, 7, 18, 16, 26),
    u'Request_Date': datetime(2015, 7, 18, 16, 15),
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
    u'date_inserted': datetime(2015, 7, 18, 17, 0, 2, 240000),
    u'id': 5949264,
    u'last_updated': datetime(2015, 7, 18, 17, 0, 2, 240000),
    u'visible': u'Y'
}


class PathologyRowTestCase(OpalTestCase):
    def get_row(self, **kwargs):
        raw_data = copy.copy(FAKE_PATHOLOGY_DATA)
        raw_data.update(kwargs)
        return prod_api.PathologyRow(raw_data)

    def test_get_hospital_number(self):
        row = self.get_row(
            Patient_Number="1232",
        )
        self.assertEqual(row.hospital_number, "1232")

    def test_get_nhs_number(self):
        row = self.get_row(
            CRS_NHS_Number="1232",
        )
        self.assertEqual(row.nhs_number, "1232")

        row = self.get_row(
            CRS_NHS_Number="",
            Patient_ID_External="1232"
        )

        self.assertEqual(row.nhs_number, "1232")

    def test_get_surname(self):
        row = self.get_row(
            CRS_Surname="Rubble"
        )
        self.assertEqual(row.surname, "Rubble")

        row = self.get_row(
            CRS_Surname="",
            Surname="Rubble"
        )

        self.assertEqual(row.surname, "Rubble")

    def test_first_name(self):
        row = self.get_row(
            CRS_Forename1="Betty"
        )
        self.assertEqual(row.first_name, "Betty")

        row = self.get_row(
            CRS_Forename1="",
            Firstname="Betty"
        )

        self.assertEqual(row.first_name, "Betty")

    def test_get_sex_male(self):
        row = self.get_row(
            CRS_SEX="M"
        )
        self.assertEqual(row.sex, "Male")

        row = self.get_row(
            CRS_SEX="",
            SEX="M"
        )

        self.assertEqual(row.sex, "Male")

    def test_get_sex_female(self):
        row = self.get_row(
            CRS_SEX="F"
        )
        self.assertEqual(row.sex, "Female")

        row = self.get_row(
            CRS_SEX="",
            SEX="F"
        )

        self.assertEqual(row.sex, "Female")

    def test_get_ethnicity(self):
        row = self.get_row(
            CRS_Ethnic_Group="A"
        )
        self.assertEqual(row.ethnicity, "White - British")

    def test_get_date_of_birth(self):
        dt = datetime(2017, 10, 1)
        row = self.get_row(
            CRS_DOB=dt
        )
        self.assertEqual(row.date_of_birth, "01/10/2017")

        row = self.get_row(
            CRS_DOB="",
            date_of_birth=dt
        )

        self.assertEqual(row.date_of_birth, "01/10/2017")

    def test_get_title(self):
        expected = "Ms"
        row = self.get_row(
            CRS_Title="Ms"
        )
        self.assertEqual(row.title, expected)

        row = self.get_row(
            CRS_Title="",
            title="Ms"
        )
        self.assertEqual(row.title, expected)

    def test_get_demographics_dict(self):
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

    def test_get_reference_range(self):
        row = self.get_row(Result_Range="10 - 2")
        self.assertEqual(
            row.reference_range,
            "10 - 2"
        )

    def test_get_status(self):
        row = self.get_row(OBX_Status="F")
        self.assertEqual(
            row.status, lmodels.LabTest.COMPLETE
        )

        row = self.get_row(OBX_Status="C")
        self.assertEqual(
            row.status, lmodels.LabTest.PENDING
        )

    def test_get_test_code(self):
        row = self.get_row(OBR_exam_code_ID="123")
        self.assertEqual(
            row.test_code, "123"
        )

    def test_get_test_name(self):
        row = self.get_row(OBR_exam_code_Text="Blood Cultures")
        self.assertEqual(
            row.test_name, "Blood Cultures"
        )

    def test_get_results_dict(self):
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

    def test_get_all_fields(self):
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


FAKE_MAIN_DEMOGRAPHICS_ROW = {
    u'PATIENT_NUMBER': u'20552710',
    u'NHS_NUMBER': u'111',
    u'FORENAME1': u'TEST',
    u'SURNAME': u'ZZZTEST',
    u'DOB': datetime(1980, 10, 10, 0, 0),
    u'SEX': u'F',
    u'ETHNIC_GROUP': u'D',
    u'TITLE': u'Ms',
}

@override_settings(
    HOSPITAL_DB=dict(
        IP_ADDRESS="0.0.0.0",
        DATABASE="made_up",
        USERNAME="some_username",
        PASSWORD="some_password",
        VIEW="some_view"
    )
)
class ProdApiTestcase(OpalTestCase):
    def get_api(self):
        return prod_api.ProdApi()

    def get_row(self, **kwargs):
        raw_data = copy.copy(FAKE_PATHOLOGY_DATA)
        raw_data.update(kwargs)
        return prod_api.PathologyRow(raw_data)

    def test_init(self):
        api = prod_api.ProdApi()
        self.assertEqual(
            api.view, "some_view"
        )

    @mock.patch('intrahospital_api.apis.prod_api.pytds')
    def test_execute_query_with_params(self, pytds):
        api = self.get_api()
        conn = pytds.connect().__enter__()
        cursor = conn.cursor().__enter__()
        cursor.fetchall.return_value = ["some_results"]
        result = api.execute_query(
            "some query", dict(hospital_number="1231222222")
        )
        self.assertEqual(
            result, ["some_results"]
        )
        cursor.execute.assert_called_once_with(
            "some query",
            dict(hospital_number="1231222222")
        )
        self.assertTrue(cursor.fetchall.called)

    @mock.patch('intrahospital_api.apis.prod_api.pytds')
    def test_execute_query_without_params(self, pytds):
        api = self.get_api()
        conn = pytds.connect().__enter__()
        cursor = conn.cursor().__enter__()
        cursor.fetchall.return_value = ["some_results"]
        result = api.execute_query("some query")
        self.assertEqual(
            result, ["some_results"]
        )
        cursor.execute.assert_called_once_with("some query", None)
        self.assertTrue(cursor.fetchall.called)

    @mock.patch("intrahospital_api.apis.prod_api.datetime.date")
    def test_raw_data(self, dt):
        dt.today.return_value = date(2017, 10, 1)
        api = self.get_api()
        expected = [copy.copy(FAKE_PATHOLOGY_DATA)]
        with mock.patch.object(api, 'execute_query') as execute_query:
            execute_query.return_value = [copy.copy(FAKE_PATHOLOGY_DATA)]
            result = api.raw_data("12312222")
        self.assertEqual(result, expected)

        # make sure we query by the correct db date
        expected_query = "SELECT * FROM some_view WHERE Patient_Number = \
@hospital_number AND last_updated > @since ORDER BY last_updated DESC;"
        self.assertEqual(
            execute_query.call_args[0][0], expected_query
        )
        self.assertEqual(
            execute_query.call_args[1]["params"], dict(
                hospital_number="12312222",
                since=date(2016, 10, 1)
            )
        )

    def test_cooked_data(self):
        api = self.get_api()
        with mock.patch.object(api, "raw_data") as raw_data:
            raw_data.return_value = [copy.copy(FAKE_PATHOLOGY_DATA)]
            rows = api.cooked_data("123")
        self.assertEqual(len(list(rows)), 1)

    def test_pathology_demographics_success(self):
        api = self.get_api()
        with mock.patch.object(api, "execute_query") as execute_query:
            execute_query.return_value = [FAKE_PATHOLOGY_DATA]
            result = api.pathology_demographics("123")

        self.assertEqual(
            result["first_name"], "TEST"
        )

        expected_query = "SELECT top(1) * FROM some_view WHERE Patient_Number \
= @hospital_number ORDER BY last_updated DESC;"
        self.assertEqual(
            execute_query.call_args[0][0], expected_query
        )
        self.assertEqual(
            execute_query.call_args[1]["params"], dict(hospital_number="123")
        )

    def test_pathology_demographics_hospital_number_fail(self):
        api = self.get_api()
        with mock.patch.object(api, "execute_query") as execute_query:
            execute_query.return_value = []
            result = api.pathology_demographics("A1' 23")

        self.assertIsNone(result)

    def test_main_demographics_success(self):
        api = self.get_api()
        with mock.patch.object(api, "execute_query") as execute_query:
            execute_query.return_value = [FAKE_MAIN_DEMOGRAPHICS_ROW]
            result = api.main_demographics("123")

        self.assertEqual(
            result["first_name"], "TEST"
        )

        self.assertEqual(
            result["surname"], "ZZZTEST"
        )
        self.assertEqual(
            result["hospital_number"], "20552710"
        )
        self.assertEqual(
            result["date_of_birth"], "10/10/1980"
        )
        self.assertEqual(
            result["sex"], "Female"
        )
        self.assertEqual(
            result["title"], "Ms"
        )
        self.assertEqual(
            result["ethnicity"], "Mixed - White and Black Caribbean"
        )

        expected_query = "SELECT top(1) * FROM VIEW_CRS_Patient_Masterfile WHERE Patient_Number \
= @hospital_number ORDER BY last_updated DESC;"
        self.assertEqual(
            execute_query.call_args[0][0], expected_query
        )
        self.assertEqual(
            execute_query.call_args[1]["params"], dict(hospital_number="123")
        )

    def test_main_demographics_fail(self):
        api = self.get_api()
        with mock.patch.object(api, "execute_query") as execute_query:
            execute_query.return_value = []
            result = api.main_demographics("A1' 23")

        self.assertIsNone(result)

    def test_demographics_found_in_main(self):
        api = self.get_api()
        with mock.patch.object(api, "main_demographics") as main_demographics:
            with mock.patch.object(api, "pathology_demographics") as pathology_demographics:
                main_demographics.return_value = dict(first_name="Wilma")
                result = api.demographics("111")

        self.assertEqual(
            result,
            dict(first_name="Wilma", external_system=constants.EXTERNAL_SYSTEM)
        )

        main_demographics.assert_called_once_with("111")
        self.assertFalse(pathology_demographics.called)

    def test_demographics_found_in_pathology(self):
        api = self.get_api()
        with mock.patch.object(api, "main_demographics") as main_demographics:
            with mock.patch.object(api, "pathology_demographics") as pathology_demographics:
                main_demographics.return_value = None
                pathology_demographics.return_value = dict(first_name="Wilma")
                result = api.demographics("111")

        self.assertEqual(
            result,
            dict(first_name="Wilma", external_system=constants.EXTERNAL_SYSTEM)
        )

        main_demographics.assert_called_once_with("111")
        pathology_demographics.assert_called_once_with("111")

    def test_demographics_not_found_in_either(self):
        api = self.get_api()

        with mock.patch.object(api, "execute_query") as execute_query:
            execute_query.return_value = []
            result = api.demographics("123")

        self.assertIsNone(result)

    def test_data_deltas(self):
        api = self.get_api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )
        expected_result = [{
            'demographics': {
                'nhs_number': u'7060976728',
                'first_name': u'TEST',
                'surname': u'ZZZTEST',
                'title': '',
                'sex': 'Female',
                'hospital_number': u'20552710',
                'date_of_birth': '10/10/1980',
                'ethnicity': 'Mixed - White and Black Caribbean'
            },
            'lab_tests': [{
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
        }]
        with mock.patch.object(api, "data_delta_query") as execute_query:
            expected = [
                self.get_row()
            ]
            execute_query.return_value = expected
            since = datetime.now()
            result = api.data_deltas(since)
        self.assertEqual(
            result, expected_result
        )

    def test_data_deltas_none(self):
        """
        If the db query does not return anything
        we should return an empty iterator
        """

        api = self.get_api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            expected = []
            execute_query.return_value = expected
            since = datetime.now()
            result = api.data_deltas(since)
        self.assertEqual(
            result, []
        )

    def test_data_deltas_no_patient(self):
        """
        If the db query return something but we have
        no match patient, we should return an empty
        iterator
        """
        api = self.get_api()
        patient, _ = self.new_patient_and_episode_please()
        # a different hospital number to the one returned
        patient.demographics_set.update(
            hospital_number='20552711'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            expected = [self.get_row()]
            execute_query.return_value = expected
            since = datetime.now()
            result = api.data_deltas(since)
        self.assertEqual(
            result, []
        )

    def test_data_deltas_multiple_tests(self):
        """
        If there are multiple tests for a patient
        we should see this in the output
        """
        expected = [
            self.get_row(Result_ID="122"),
            self.get_row(Result_ID="123")
        ]
        expected_result = [{
            'demographics': {
                'nhs_number': u'7060976728',
                'first_name': u'TEST',
                'surname': u'ZZZTEST',
                'title': '',
                'sex': 'Female',
                'hospital_number': u'20552710',
                'date_of_birth': '10/10/1980',
                'ethnicity': 'Mixed - White and Black Caribbean'
            },
            'lab_tests': [
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
        }]

        api = self.get_api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            execute_query.return_value = expected
            since = datetime.now()
            result = api.data_deltas(since)
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
        expected_result = [{
            'demographics': {
                'nhs_number': u'7060976728',
                'first_name': u'TEST',
                'surname': u'ZZZTEST',
                'title': '',
                'sex': 'Female',
                'hospital_number': u'20552710',
                'date_of_birth': '10/10/1980',
                'ethnicity': 'Mixed - White and Black Caribbean'
            },
            'lab_tests': [
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
        }]

        api = self.get_api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            execute_query.return_value = expected
            since = datetime.now()
            result = api.data_deltas(since)
        self.assertEqual(
            result, expected_result
        )

    def test_data_deltas_multiple_observations(self):
        """
        Multiple observations with the same lab test
        number should be aggregated
        """
        expected = [
            self.get_row(Result_ID="122", OBX_id=20334311),
            self.get_row(Result_ID="122", OBX_id=20334312)
        ]
        expected_result = [{
            'demographics': {
                'nhs_number': u'7060976728',
                'first_name': u'TEST',
                'surname': u'ZZZTEST',
                'title': '',
                'sex': 'Female',
                'hospital_number': u'20552710',
                'date_of_birth': '10/10/1980',
                'ethnicity': 'Mixed - White and Black Caribbean'
            },
            'lab_tests': [
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
        }]

        api = self.get_api()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number='20552710'
        )

        with mock.patch.object(api, "data_delta_query") as execute_query:
            execute_query.return_value = expected
            since = datetime.now()
            result = api.data_deltas(since)
        self.assertEqual(
            result, expected_result
        )

    def test_data_deltas_multiple_patients(self):
        """
        Multiple patients with lab tests
        """
        self.maxDiff = None
        expected = [
            self.get_row(Patient_Number="123", Result_ID="124"),
            self.get_row(Patient_Number="125", Result_ID="126"),
        ]
        expected_result = [
            {
                'demographics': {
                    'nhs_number': u'7060976728',
                    'first_name': u'TEST',
                    'surname': u'ZZZTEST',
                    'title': '',
                    'sex': 'Female',
                    'hospital_number': u'123',
                    'date_of_birth': '10/10/1980',
                    'ethnicity': 'Mixed - White and Black Caribbean'
                },
                'lab_tests': [
                    {
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
                    },

                ]
            },
            {
                'demographics': {
                    'nhs_number': u'7060976728',
                    'first_name': u'TEST',
                    'surname': u'ZZZTEST',
                    'title': '',
                    'sex': 'Female',
                    'hospital_number': u'125',
                    'date_of_birth': '10/10/1980',
                    'ethnicity': 'Mixed - White and Black Caribbean'
                },
                'lab_tests': [
                    {
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
                    },

                ]
            }
        ]

        api = self.get_api()
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
            since = datetime.now()
            result = api.data_deltas(since)
        self.assertEqual(
            result, expected_result
        )
