import datetime
import json
from functools import wraps
import pytds
import itertools
import time
from collections import defaultdict
from pytds.tds import OperationalError
from intrahospital_api.apis import base_api
from intrahospital_api.apis import db
from intrahospital_api import logger
from intrahospital_api.constants import EXTERNAL_SYSTEM
from elcid.utils import timing
from lab import models as lmodels
from django.conf import settings
from elcid.models import Demographics

# if we fail in a query, the amount of seconds we wait before retrying
RETRY_DELAY = 30

MAIN_DEMOGRAPHICS_VIEW = "VIEW_CRS_Patient_Masterfile"

PATHOLOGY_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;"

MAIN_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;"

ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since ORDER BY last_updated DESC;"

ALL_DATA_QUERY_WITH_LAB_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since and Result_ID = @lab_number ORDER BY last_updated DESC;"

ALL_DATA_QUERY_WITH_LAB_TEST_TYPE = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since and OBR_exam_code_Text = @test_type ORDER BY last_updated DESC;"

ALL_DATA_SINCE = "SELECT * FROM {view} WHERE last_updated > @since ORDER BY Patient_Number, last_updated DESC;"


ETHNICITY_MAPPING = {
    "99": "Other - Not Known",
    "A": "White - British",
    "B": "White - Irish",
    "C": "White - Any Other White Background",
    "D": "Mixed - White and Black Caribbean",
    "E": "Mixed - White and Black African",
    "F": "Mixed - White and Asian",
    "G": "Mixed - Any Other Mixed Background",
    "H": "Asian or Asian British - Indian",
    "J": "Asian or Asian British - Pakistani",
    "K": "Asian or Asian British - Bangladeshi",
    "L": "Asian - Any Other Asian Background",
    "M": "Black or Black British - Caribbean",
    "N": "Black or Black British - African",
    "P": "Black - Any Other Black Background",
    "R": "Other - Chinese",
    "S": "Other - Any Other Ethnic Group",
    "Z": "Other - Not Stated",
}


class MainDemographicsRow(db.Row):
    FIELD_MAPPINGS = dict(
        hospital_number="PATIENT_NUMBER",
        nhs_number="NHS_NUMBER",
        first_name="FORENAME1",
        surname="SURNAME",
        date_of_birth="date_of_birth",
        sex="sex",
        ethnicity="ethnicity",
        title="TITLE"
    )

    @property
    def date_of_birth(self):
        dob = self.raw_data.get("DOB")
        if dob:
            return db.to_date_str(dob.date())

    @property
    def sex(self):
        sex_abbreviation = self.raw_data.get("SEX")

        if sex_abbreviation:
            if sex_abbreviation == "M":
                return "Male"
            else:
                return "Female"
    @property
    def ethnicity(self):
        return ETHNICITY_MAPPING.get(self.raw_data.get("ETHNIC_GROUP"))

    def get_demographics_dict(self):
        result = {}
        for field in self.FIELD_MAPPINGS:
            result[field] = getattr(self, field)
        return result


class PathologyRow(db.Row):
    """ a simple wrapper to get us the fields we actually want out of a row
    """
    DEMOGRAPHICS_MAPPING = dict(
        hospital_number="Patient_Number",
        nhs_number=("CRS_NHS_Number", "Patient_ID_External",),
        first_name=("CRS_Forename1", "Firstname",),
        surname=("CRS_Surname", "Surname",),
        date_of_birth="date_of_birth",
        sex="sex",
        ethnicity="ethnicity",
        title=("CRS_Title", "title",)
    )

    LAB_TEST_MAPPING = dict(
        clinical_info="Relevant_Clinical_Info",
        datetime_ordered="datetime_ordered",
        external_identifier="Result_ID",
        site="site",
        status="status",
        test_code="OBR_exam_code_ID",
        test_name="OBR_exam_code_Text",
    )

    OBSERVATION_MAPPING = dict(
        last_updated="last_updated",
        observation_datetime="observation_datetime",
        observation_name="OBX_exam_code_Text",
        observation_number="OBX_id",
        observation_value="Result_Value",
        reference_range="Result_Range",
        units="Result_Units"
    )

    RESULT_MAPPING = dict(
        OBSERVATION_MAPPING.items() + LAB_TEST_MAPPING.items()
    )

    FIELD_MAPPINGS = dict(
        RESULT_MAPPING.items() + DEMOGRAPHICS_MAPPING.items()
    )

    @property
    def sex(self):
        sex_abbreviation = self._get_or_fallback("CRS_SEX", "SEX")

        if sex_abbreviation == "M":
            return "Male"
        else:
            return "Female"

    @property
    def ethnicity(self):
        return ETHNICITY_MAPPING.get(self.raw_data.get("CRS_Ethnic_Group"))

    @property
    def date_of_birth(self):
        dob = self._get_or_fallback("CRS_DOB", "date_of_birth")
        if dob:
            return db.to_date_str(dob.date())

    def get_demographics_dict(self):
        result = {}
        for key in self.DEMOGRAPHICS_MAPPING.keys():
            result[key] = getattr(self, key)
        return result

    @property
    def status(self):
        status_abbr = self.raw_data.get("OBX_Status")

        if status_abbr == 'F':
            return lmodels.LabTest.COMPLETE
        else:
            return lmodels.LabTest.PENDING

    @property
    def site(self):
        site = self.raw_data.get('Specimen_Site')
        if "^" in site and "-" in site:
            return site.split("^")[1].strip().split("-")[0].strip()
        return site

    @property
    def datetime_ordered(self):
        return db.to_datetime_str(
            self.raw_data.get(
                "Observation_date", self.raw_data.get("Request_Date")
            )
        )

    @property
    def observation_datetime(self):
        dt = self.raw_data.get("Observation_date")
        dt = dt or self.raw_data.get("Request_Date")
        return db.to_datetime_str(dt)

    @property
    def last_updated(self):
        return db.to_datetime_str(self.raw_data.get("last_updated"))

    def get_dict(self, name):
        result = {}
        mapping = getattr(self, name)

        for field in mapping.keys():
            result[field] = getattr(self, field)

        return result

    def get_results_dict(self):
        return self.get_dict("RESULT_MAPPING")

    def get_lab_test_dict(self):
        return self.get_dict("LAB_TEST_MAPPING")

    def get_observation_dict(self):
        return self.get_dict("OBSERVATION_MAPPING")

    def get_all_fields(self):
        return self.get_dict("FIELD_MAPPINGS")


class ProdApi(db.DBConnection, base_api.BaseApi):
    def __init__(self):
        super(ProdApi, self).__init__()
        self.view = settings.HOSPITAL_DB["VIEW"]

    def execute_query(self, query, params=None):
        with pytds.connect(
            self.ip_address,
            self.database,
            self.username,
            self.password,
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                logger.info(
                    "Running upstream query {} {}".format(query, params)
                )
                cur.execute(query, params)
                result = cur.fetchall()
        logger.info(result)
        return result

    @property
    def pathology_demographics_query(self):
        return PATHOLOGY_DEMOGRAPHICS_QUERY.format(view=self.view)

    @property
    def all_data_for_hospital_number_query(self):
        return ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER.format(view=self.view)

    @property
    def all_data_since_query(self):
        return ALL_DATA_SINCE.format(view=self.view)

    @property
    def all_data_query_for_lab_number(self):
        return ALL_DATA_QUERY_WITH_LAB_NUMBER.format(view=self.view)

    @property
    def all_data_query_for_lab_test_type(self):
        return ALL_DATA_QUERY_WITH_LAB_TEST_TYPE.format(view=self.view)

    @property
    def main_demographics_query(self):
        return MAIN_DEMOGRAPHICS_QUERY.format(view=MAIN_DEMOGRAPHICS_VIEW)

    def demographics(self, hospital_number):
        hospital_number = hospital_number.strip()

        demographics_result = self.main_demographics(hospital_number)

        if not demographics_result:
            demographics_result = self.pathology_demographics(hospital_number)

        if demographics_result:
            demographics_result["external_system"] = EXTERNAL_SYSTEM
            return demographics_result

    @timing
    @db.db_retry
    def main_demographics(self, hospital_number):
        rows = list(self.execute_query(
            self.main_demographics_query,
            params=dict(hospital_number=hospital_number)
        ))
        if not len(rows):
            return

        return MainDemographicsRow(rows[0]).get_demographics_dict()


    @timing
    @db.db_retry
    def pathology_demographics(self, hospital_number):
        rows = list(self.execute_query(
            self.pathology_demographics_query,
            params=dict(hospital_number=hospital_number)
        ))
        if not len(rows):
            return

        return PathologyRow(rows[0]).get_demographics_dict()

    def raw_data(self, hospital_number, lab_number=None, test_type=None):
        """ not all data, I lied. Only the last year's
        """
        db_date = datetime.date.today() - datetime.timedelta(365)

        if lab_number:
            return self.execute_query(
                self.all_data_query_for_lab_number,
                params=dict(
                    hospital_number=hospital_number,
                    since=db_date,
                    lab_number=lab_number
                )
            )
        if test_type:
            return self.execute_query(
                self.all_data_query_for_lab_test_type,
                params=dict(
                    hospital_number=hospital_number,
                    since=db_date,
                    test_type=test_type
                )
            )
        else:
            return self.execute_query(
                self.all_data_for_hospital_number_query,
                params=dict(hospital_number=hospital_number, since=db_date)
            )

    @timing
    @db.db_retry
    def data_delta_query(self, since):
        all_rows = self.execute_query(
            self.all_data_since_query,
            params=dict(since=since)
        )
        return (PathologyRow(r) for r in all_rows)

    def data_deltas(self, some_datetime):
        """ yields an iterator of dictionary

            the dictionary contains

            "demographics" : demographics, the first (ie the most recent)
            demographics result in the set.

            "lab_tests": all lab tests for the patient

        """
        all_rows = self.data_delta_query(some_datetime)

        hospital_number_to_rows = defaultdict(list)

        for row in all_rows:
            hospital_number_to_rows[row.hospital_number].append(row)

        result = []

        for hospital_number, rows in hospital_number_to_rows.items():
            if Demographics.objects.filter(
                hospital_number=hospital_number
            ).exists():
                demographics = rows[0].get_demographics_dict()
                lab_tests = self.cast_rows_to_lab_test(rows)
                result.append(dict(
                    demographics=demographics,
                    lab_tests=lab_tests
                ))

        return result

    def cooked_data(self, hospital_number):
        raw_data = self.raw_data(hospital_number)
        return (PathologyRow(row).get_all_fields() for row in raw_data)

    def cast_rows_to_lab_test(self, rows):
        """ We cast multiple rows to lab tests.

            A lab test number(external identifier) can have multiple lab test
            types and multiple obsevartions.

            So we split the rows (observations) up via lab number/lab test type

        """
        lab_number_type_to_observations = defaultdict(list)
        lab_number_type_to_lab_test = dict()

        for row in rows:
            lab_test_dict = row.get_lab_test_dict()
            lab_number = lab_test_dict["external_identifier"]
            lab_test_type = lab_test_dict["test_name"]
            lab_number_type_to_lab_test[
                (lab_number, lab_test_type,)
            ] = lab_test_dict
            lab_number_type_to_observations[
                (lab_number, lab_test_type,)
            ].append(
                row.get_observation_dict()
            )
        result = []

        for external_id_and_type, lab_test in lab_number_type_to_lab_test.items():
            lab_test = lab_number_type_to_lab_test[external_id_and_type]
            lab_test["observations"] = lab_number_type_to_observations[
                external_id_and_type
            ]
            lab_test["external_system"] = EXTERNAL_SYSTEM
            result.append(lab_test)
        return result

    @timing
    def results_for_hospital_number(self, hospital_number):
        """
            returns all the results for a particular person

            aggregated into labtest: observations([])
        """

        raw_rows = self.raw_data(hospital_number)
        rows = (PathologyRow(raw_row) for raw_row in raw_rows)
        return self.cast_rows_to_lab_test(rows)
