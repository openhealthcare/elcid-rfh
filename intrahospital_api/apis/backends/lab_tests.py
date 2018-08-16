import datetime
import logging
import itertools
from collections import defaultdict
from django.conf import settings
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api.apis.backends import db
from elcid.utils import timing
from lab import models as lmodels
from elcid.models import Demographics

logger = logging.getLogger('intrahospital_api')
VIEW = "Pathology_Result_view"


DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;".format(view=VIEW)

ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since ORDER BY last_updated DESC;".format(
    view=VIEW
)

ALL_DATA_QUERY_WITH_LAB_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since and Result_ID = @lab_number \
ORDER BY last_updated DESC;"

ALL_DATA_QUERY_WITH_LAB_TEST_TYPE = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since and OBR_exam_code_Text = \
@test_type ORDER BY last_updated DESC;".format(view=VIEW)

ALL_DATA_SINCE = "SELECT * FROM {view} WHERE last_updated > @since ORDER BY \
Patient_Number, last_updated DESC;".format(view=VIEW)


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


class Row(db.Row):
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
        test_code="OBX_exam_code_ID",
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

    FIELD_MAPPINGS = dict(
        OBSERVATION_MAPPING.items() + LAB_TEST_MAPPING.items() + DEMOGRAPHICS_MAPPING.items()
    )

    def __init__(self, db_row):
        self.db_row = db_row

    @property
    def sex(self):
        sex_abbreviation = self.get_or_fallback("CRS_SEX", "SEX")

        if sex_abbreviation == "M":
            return "Male"
        else:
            return "Female"

    @property
    def ethnicity(self):
        return ETHNICITY_MAPPING.get(self.db_row.get("CRS_Ethnic_Group"))

    @property
    def date_of_birth(self):
        dob = self.get_or_fallback("CRS_DOB", "date_of_birth")
        if dob:
            return db.to_date_str(dob.date())

    @property
    def status(self):
        status_abbr = self.db_row.get("OBX_Status")

        if status_abbr == 'F':
            return lmodels.LabTest.COMPLETE
        else:
            return lmodels.LabTest.PENDING

    @property
    def site(self):
        site = self.db_row.get('Specimen_Site')
        if "^" in site and "-" in site:
            return site.split("^")[1].strip().split("-")[0].strip()
        return site

    @property
    def datetime_ordered(self):
        return db.to_datetime_str(
            self.db_row.get(
                "Observation_date", self.db_row.get("Request_Date")
            )
        )

    @property
    def observation_datetime(self):
        dt = self.db_row.get("Observation_date")
        dt = dt or self.db_row.get("Request_Date")
        return db.to_datetime_str(dt)

    @property
    def last_updated(self):
        return db.to_datetime_str(self.db_row.get("last_updated"))

    def get_demographics_dict(self):
        result = {}
        for field in self.DEMOGRAPHICS_MAPPING.keys():
            result[field] = self[field]
        return result

    def get_results_dict(self):
        result = {}
        result_keys = self.OBSERVATION_MAPPING.keys()
        result_keys = result_keys + self.LAB_TEST_MAPPING.keys()
        for field in result_keys:
            result[field] = self[field]

        return result

    def get_lab_test_dict(self):
        result = {}
        lab_test_keys = list(self.LAB_TEST_MAPPING.keys())
        lab_test_keys = lab_test_keys + list(self.OBSERVATION_MAPPING.keys())
        for field in lab_test_keys:
            result[field] = self[field]
        return result

    def get_observation_dict(self):
        result = {}
        for field in self.OBSERVATION_MAPPING.keys()():
            result[field] = self[field]
        return result

    def get_all_fields(self):
        result = {}
        for field in self.FIELD_MAPPINGS.keys():
            result[field] = self[field]
        return result


class LabTestApi(object):
    def __init__(self):
        self.connection = db.DBConnection()

    @timing
    def demographics(self, hospital_number):
        hospital_number = hospital_number.strip()
        rows = list(self.connection.execute_query(
            DEMOGRAPHICS_QUERY,
            hospital_number=hospital_number
        ))
        if not len(rows):
            return

        demographics_dict = Row(rows[0]).get_demographics_dict()
        demographics_dict["external_system"] = EXTERNAL_SYSTEM
        return demographics_dict

    def raw_lab_tests(self, hospital_number, lab_number=None, test_type=None):
        """ not all data, I lied. Only the last year's
        """
        db_date = datetime.date.today() - datetime.timedelta(365)

        if lab_number:
            return self.connection.execute_query(
                ALL_DATA_QUERY_WITH_LAB_NUMBER,
                hospital_number=hospital_number,
                since=db_date,
                lab_number=lab_number
            )
        if test_type:
            return self.connection.execute_query(
                ALL_DATA_QUERY_WITH_LAB_TEST_TYPE,
                hospital_number=hospital_number,
                since=db_date,
                test_type=test_type
            )
        else:
            return self.connection.execute_query(
                ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER,
                hospital_number=hospital_number, since=db_date
            )

    @timing
    def data_delta_query(self, since):
        all_rows = self.connection.execute_query(
            ALL_DATA_SINCE,
            since=since
        )
        return (Row(r) for r in all_rows)

    def lab_test_results_since(self, some_datetime):
        """ yields an iterator of dictionary

            the dictionary contains

            "demographics" : demographics, the first (ie the most recent)
            demographics result in the set.

            "lab_tests": all lab tests for the patient

        """
        all_rows = self.data_delta_query(some_datetime)
        hospital_number_to_rows = itertools.groupby(
            all_rows, lambda x: x.get_hospital_number()
        )
        for hospital_number, rows in hospital_number_to_rows:
            if Demographics.objects.filter(
                hospital_number=hospital_number
            ).exists():
                demographics = list(rows)[0].get_demographics_dict()
                lab_tests = self.cast_rows_to_lab_test(rows)
                yield (
                    dict(
                        demographics=demographics,
                        lab_tests=lab_tests
                    )
                )

    def cooked_lab_tests(self, hospital_number):
        raw_lab_tests = self.raw_lab_tests(hospital_number)
        return (Row(row).get_all_fields() for row in raw_lab_tests)

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
    def lab_tests_for_hospital_number(self, hospital_number):
        """
            returns all the results for a particular person

            aggregated into labtest: observations([])
        """

        raw_rows = self.raw_lab_tests(hospital_number)
        rows = (Row(raw_row) for raw_row in raw_rows)
        return self.cast_rows_to_lab_test(rows)
