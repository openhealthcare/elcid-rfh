import copy
import mock
import datetime
from opal.core.test import OpalTestCase
from lab import models as lmodels
from intrahospital_api.services.demographics.backends import live as demographics
from intrahospital_api import constants

FAKE_PATHOLOGY_ROW_DATA = {
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

FAKE_MAIN_DEMOGRAPHICS_ROW = {
    u'PATIENT_NUMBER': u'20552710',
    u'NHS_NUMBER': u'111',
    u'FORENAME1': u'TEST',
    u'SURNAME': u'ZZZTEST',
    u'DOB': datetime.datetime(1980, 10, 10, 0, 0),
    u'SEX': u'F',
    u'ETHNIC_GROUP': u'D',
    u'TITLE': u'Ms',
}


class PathologyDemographicsRowTestCase(OpalTestCase):
    maxDiff = None

    def get_row(self, **kwargs):
        raw_demographics = copy.copy(FAKE_PATHOLOGY_ROW_DATA)
        raw_demographics.update(kwargs)
        return demographics.PathologyDemographicsRow(raw_demographics)

    def test_sex_female(self):
        row = self.get_row(
            CRS_SEX="F"
        )
        self.assertEqual(row.sex, "Female")

    def test_sex_not_set(self):
        row = self.get_row(
            CRS_SEX="",
            SEX=""
        )
        self.assertIsNone(row.sex)

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


class MainDemographicsTestCase(OpalTestCase):
    def get_row(self, **kwargs):
        raw_demographics = copy.copy(FAKE_MAIN_DEMOGRAPHICS_ROW)
        raw_demographics.update(kwargs)
        return demographics.MainDemographicsRow(raw_demographics)

    def test_date_of_birth(self):
        dt = datetime.datetime(2017, 10, 1)
        row = self.get_row(
            DOB=dt
        )
        self.assertEqual(row["date_of_birth"], "01/10/2017")

    def test_sex_male(self):
        row = self.get_row(
            SEX="M"
        )
        self.assertEqual(row["sex"], "Male")

    def test_sex_female(self):
        row = self.get_row(
            SEX="F"
        )
        self.assertEqual(row["sex"], "Female")

    def test_sex_none(self):
        row = self.get_row(
            SEX=""
        )
        self.assertIsNone(row.sex)

    def test_ethnicity(self):
        row = self.get_row(
            ETHNIC_GROUP="A"
        )
        self.assertEqual(row["ethnicity"], "White - British")

    def test_title(self):
        row = self.get_row(
            Title="Ms"
        )
        self.assertEqual(row["title"], "Ms")


class DemographicsApiTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        super(DemographicsApiTestCase, self).setUp(*args, **kwargs)
        self.api = demographics.Api()

    def run_demographics_for_hospital_number(
        self, pathology_return, main_return
    ):

        with mock.patch.object(
            self.api, "pathology_demographics_for_hospital_number"
        ) as pdhn:
            if pathology_return is None:
                pdhn.return_value = pathology_return
            else:
                pdhn.return_value[0].translate.return_value = pathology_return
            with mock.patch.object(
                self.api, "main_demographics_for_hospital_number"
            ) as mdhn:
                if main_return is None:
                    mdhn.return_value = main_return
                else:
                    mdhn.return_value[0].translate.return_value = main_return
                result = self.api.demographics_for_hospital_number("111")
        return result, pdhn, mdhn

    def test_demographics_for_hospital_number_main_found(self):
        pathology_return = {"hospital_number": "1"}
        main_return = {"hospital_number": "2"}
        result, pdhn, mdhn = self.run_demographics_for_hospital_number(
            pathology_return, main_return
        )
        self.assertEqual(
            result,
            dict(
                hospital_number="2",
                external_system=constants.EXTERNAL_SYSTEM
            )
        )
        mdhn.assert_called_once_with("111")
        self.assertFalse(pdhn.called)

    def test_demographics_for_hospital_number_pathology_found(self):
        pathology_return = {"hospital_number": "1"}
        main_return = None
        result, pdhn, mdhn = self.run_demographics_for_hospital_number(
            pathology_return, main_return
        )
        self.assertEqual(
            result,
            dict(
                hospital_number="1",
                external_system=constants.EXTERNAL_SYSTEM
            )
        )
        mdhn.assert_called_once_with("111")
        pdhn.assert_called_once_with("111")

    def test_demographics_for_hospital_number_none_found(self):
        pathology_return = None
        main_return = None
        result, pdhn, mdhn = self.run_demographics_for_hospital_number(
            pathology_return, main_return
        )
        self.assertIsNone(result)
        mdhn.assert_called_once_with("111")
        pdhn.assert_called_once_with("111")
