import datetime
import json
from functools import wraps
import pytds
import itertools
import time
from collections import defaultdict
from pytds.tds import OperationalError
from intrahospital_api.apis import base_api
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
@hospital_number ORDER BY date_inserted DESC;"

MAIN_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;"

ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND date_inserted > @since ORDER BY date_inserted DESC;"

ALL_DATA_QUERY_WITH_LAB_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND date_inserted > @since and Result_ID = @lab_number ORDER BY date_inserted DESC;"

ALL_DATA_QUERY_WITH_LAB_TEST_TYPE = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND date_inserted > @since and OBR_exam_code_Text = @test_type ORDER BY date_inserted DESC;"

ALL_DATA_SINCE = "SELECT * FROM {view} WHERE date_inserted > @since ORDER BY Patient_Number, date_inserted DESC;"


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


def to_date_str(some_date):
    """ we return something that is 'updatedable by dict'
        so we need to convert all dates into strings
    """
    if some_date:
        return some_date.strftime(settings.DATE_INPUT_FORMATS[0])


def to_datetime_str(some_datetime):
    """ we return something that is 'updatedable by dict'
        so we need to convert all datetimes into strings
    """
    if some_datetime:
        return some_datetime.strftime(settings.DATETIME_INPUT_FORMATS[0])


def db_retry(f):
    """ We are reading a database that is also receiving intermittent writes.
        When these writes are coming the DB locks.
        Lets put in a retry after 30 seconds
    """
    @wraps(f)
    def wrap(*args, **kw):
        try:
            result = f(*args, **kw)
        except OperationalError as o:
            logger.info('{}: failed with {}, retrying in {}s'.format(
                f.__name__, str(o), RETRY_DELAY
            ))
            time.sleep(RETRY_DELAY)
            result = f(*args, **kw)
        return result
    return wrap


class MainDemographicsRow(object):
    DEMOGRAPHICS_FIELDS = [
        "hospital_number",
        "nhs_number",
        "first_name",
        "surname",
        "date_of_birth",
        "sex",
        "ethnicity",
        "title"
    ]

    def __init__(self, db_row):
        self.db_row = db_row

    def get_hospital_number(self):
        return self.db_row.get("PATIENT_NUMBER")

    def get_nhs_number(self):
        return self.db_row.get("NHS_NUMBER")

    def get_first_name(self):
        return self.db_row.get("FORENAME1")

    def get_surname(self):
        return self.db_row.get("SURNAME")

    def get_date_of_birth(self):
        dob = self.db_row.get("DOB")
        if dob:
            return to_date_str(dob.date())

    def get_sex(self):
        sex_abbreviation = self.db_row.get("SEX")

        if sex_abbreviation:
            if sex_abbreviation == "M":
                return "Male"
            else:
                return "Female"

    def get_ethnicity(self):
        return ETHNICITY_MAPPING.get(self.db_row.get("ETHNIC_GROUP"))

    def get_title(self):
        return self.db_row.get("TITLE")

    def get_demographics_dict(self):
        result = {}
        for field in self.DEMOGRAPHICS_FIELDS:
            result[field] = getattr(self, "get_{}".format(field))()
        return result


class PathologyRow(object):
    """ a simple wrapper to get us the fields we actually want out of a row
    """
    DEMOGRAPHICS_FIELDS = [
        'date_of_birth',
        'date_of_birth',
        'ethnicity',
        'first_name',
        'hospital_number',
        'nhs_number',
        'sex',
        'surname',
        'title'
    ]

    LAB_TEST_FIELDS = [
        'clinical_info',
        'datetime_ordered',
        'external_identifier',
        'site',
        'status',
        'test_code',
        'test_name',
    ]

    OBSERVATION_FIELDS = [
        'last_updated',
        'observation_datetime',
        'observation_name',
        'observation_number',
        'observation_value',
        'reference_range',
        'units',
    ]

    RESULT_FIELDS = LAB_TEST_FIELDS + OBSERVATION_FIELDS

    def __init__(self, db_row):
        self.db_row = db_row

    def get_or_fallback(self, primary_field, secondary_field):
        """ look at one field, if its empty, use a different field
        """
        # we use Cerner information if it exists, otherwise
        # we fall back to winpath demographics
        # these are combined in the same table
        # so we fall back to a different
        # field name in the same row
        result = self.db_row.get(primary_field)

        if not result:
            result = self.db_row.get(secondary_field, "")

        return result

    # Demographics Fields
    def get_hospital_number(self):
        return self.db_row.get("Patient_Number")

    def get_nhs_number(self):
        return self.get_or_fallback(
            "CRS_NHS_Number", "Patient_ID_External"
        )

    def get_surname(self):
        return self.get_or_fallback("CRS_Surname", "Surname")

    def get_first_name(self):
        return self.get_or_fallback("CRS_Forename1", "Firstname")

    def get_sex(self):
        sex_abbreviation = self.get_or_fallback("CRS_SEX", "SEX")

        if sex_abbreviation == "M":
            return "Male"
        else:
            return "Female"

    def get_ethnicity(self):
        return ETHNICITY_MAPPING.get(self.db_row.get("CRS_Ethnic_Group"))

    def get_date_of_birth(self):
        dob = self.get_or_fallback("CRS_DOB", "date_of_birth")
        if dob:
            return to_date_str(dob.date())

    def get_title(self):
        return self.get_or_fallback("CRS_Title", "title")

    def get_demographics_dict(self):
        result = {}
        for field in self.DEMOGRAPHICS_FIELDS:
            result[field] = getattr(self, "get_{}".format(field))()
        return result

    def get_status(self):
        status_abbr = self.db_row.get("OBX_Status")

        if status_abbr == 'F':
            return lmodels.LabTest.COMPLETE
        else:
            return lmodels.LabTest.PENDING

    def get_site(self):
        site = self.db_row.get('Specimen_Site')
        if site and "^" in site and "-" in site:
            return site.split("^")[1].strip().split("-")[0].strip()
        return site

    def get_clinical_info(self):
        return self.db_row.get('Relevant_Clinical_Info')

    def get_test_code(self):
        return self.db_row.get('OBR_exam_code_ID')

    def get_test_name(self):
        return self.db_row.get("OBR_exam_code_Text")

    def get_external_identifier(self):
        return self.db_row.get("Result_ID")

    def get_datetime_ordered(self):
        return to_datetime_str(
            self.db_row.get(
                "Observation_date", self.db_row.get("Request_Date")
            )
        )

    # fields of the individual observations within the lab test
    def get_observation_number(self):
        return self.db_row.get("OBX_id")

    def get_observation_name(self):
        return self.db_row.get("OBX_exam_code_Text")

    def get_observation_value(self):
        return self.db_row.get('Result_Value')

    def get_units(self):
        return self.db_row.get("Result_Units")

    def get_observation_datetime(self):
        dt = self.db_row.get("Observation_date")
        dt = dt or self.db_row.get("Request_Date")
        return to_datetime_str(dt)

    def get_reference_range(self):
        return self.db_row.get("Result_Range")

    def get_last_updated(self):
        return to_datetime_str(self.db_row.get("last_updated"))

    def get_results_dict(self):
        result = {}
        for field in self.RESULT_FIELDS:
            result[field] = getattr(self, "get_{}".format(field))()

        return result

    def get_lab_test_dict(self):
        result = {}
        for field in self.LAB_TEST_FIELDS:
            result[field] = getattr(self, "get_{}".format(field))()
        return result

    def get_observation_dict(self):
        result = {}
        for field in self.OBSERVATION_FIELDS:
            result[field] = getattr(self, "get_{}".format(field))()
        return result

    def get_all_fields(self):
        result = {}
        fields = self.DEMOGRAPHICS_FIELDS + self.RESULT_FIELDS
        for field in fields:
            result[field] = getattr(self, "get_{}".format(field))()
        return result


class ProdApi(base_api.BaseApi):
    def __init__(self):
        self.hospital_settings = settings.HOSPITAL_DB
        self.trust_settings = settings.TRUST_DB
        if not all([
            self.hospital_settings.get("ip_address"),
            self.hospital_settings.get("database"),
            self.hospital_settings.get("username"),
            self.hospital_settings.get("password"),
            self.hospital_settings.get("view"),
            self.trust_settings.get("ip_address"),
            self.trust_settings.get("database"),
            self.trust_settings.get("username"),
            self.trust_settings.get("password"),
            self.trust_settings.get("view"),
        ]):
            raise ValueError(
                "You need to set proper credentials to use the prod api"
            )

    def execute_hospital_query(self, query, params=None):
        with pytds.connect(
            self.hospital_settings["ip_address"],
            self.hospital_settings["database"],
            self.hospital_settings["username"],
            self.hospital_settings["password"],
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                logger.info(
                    "Running upstream query {} {}".format(query, params)
                )
                cur.execute(query, params)
                while True:
                    latest = cur.fetchmany(1000)
                    if latest:
                        for row in latest:
                            logger.debug(row)
                            yield row
                    else:
                        break

    def execute_trust_query(self, query, params=None):
        with pytds.connect(
            self.trust_settings["ip_address"],
            self.trust_settings["database"],
            self.trust_settings["username"],
            self.trust_settings["password"],
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                logger.info(
                    "Running upstream query {} {}".format(query, params)
                )
                cur.execute(query, params)
                while True:
                    latest = cur.fetchmany(1000)
                    if latest:
                        for row in latest:
                            logger.debug(row)
                            yield row
                    else:
                        break

    @property
    def pathology_demographics_query(self):
        return PATHOLOGY_DEMOGRAPHICS_QUERY.format(
            view=self.trust_settings["view"]
        )

    @property
    def all_data_for_hospital_number_query(self):
        return ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER.format(
            view=self.trust_settings["view"]
        )

    @property
    def all_data_since_query(self):
        return ALL_DATA_SINCE.format(
            view=self.trust_settings["view"]
        )

    @property
    def all_data_query_for_lab_number(self):
        return ALL_DATA_QUERY_WITH_LAB_NUMBER.format(
            view=self.trust_settings["view"]
        )

    @property
    def all_data_query_for_lab_test_type(self):
        return ALL_DATA_QUERY_WITH_LAB_TEST_TYPE.format(
            view=self.trust_settings["view"]
        )

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
    @db_retry
    def main_demographics(self, hospital_number):
        rows = list(self.execute_hospital_query(
            self.main_demographics_query,
            params=dict(hospital_number=hospital_number)
        ))
        if not len(rows):
            return

        return MainDemographicsRow(rows[0]).get_demographics_dict()

    @timing
    @db_retry
    def pathology_demographics(self, hospital_number):
        rows = list(self.execute_trust_query(
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
            return list(self.execute_trust_query(
                self.all_data_query_for_lab_number,
                params=dict(
                    hospital_number=hospital_number,
                    since=db_date,
                    lab_number=lab_number
                )
            ))
        if test_type:
            return list(self.execute_trust_query(
                self.all_data_query_for_lab_test_type,
                params=dict(
                    hospital_number=hospital_number,
                    since=db_date,
                    test_type=test_type
                )
            ))
        else:
            return self.execute_trust_query(
                self.all_data_for_hospital_number_query,
                params=dict(hospital_number=hospital_number, since=db_date)
            )

    @timing
    @db_retry
    def data_delta_query(self, since):
        all_rows = self.execute_trust_query(
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
        hospital_numbers = set(
            Demographics.objects.values_list(
                'hospital_number', flat=True
            )
        )

        for row in all_rows:
            hn = row.get_hospital_number()
            if hn in hospital_numbers:
                hospital_number_to_rows[row.get_hospital_number()].append(row)

        result = []

        for hospital_number, rows in hospital_number_to_rows.items():
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
