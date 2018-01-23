import datetime
import logging
import traceback
import pytds
from functools import wraps
from collections import defaultdict
from intrahospital_api.apis import base_api
from lab import models as lmodels
from django.conf import settings


DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;"

ALL_DATA_QUERY = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since ORDER BY last_updated DESC;"

ALL_DATA_QUERY_WITH_LAB_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since and Result_ID = @lab_number ORDER BY last_updated DESC;"

ALL_DATA_QUERY_WITH_LAB_TEST_TYPE = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND last_updated > @since and OBR_exam_code_Text = @test_type ORDER BY last_updated DESC;"


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


def error_handler(f):
    @wraps(f)
    def wrap(*args, **kw):
        try:
            result = f(*args, **kw)
        except:
            logger = logging.getLogger('error_emailer')
            logger.error("{} threw an error".format(f.__name__))
            logger = logging.getLogger('intrahospital_api')
            logger.error(traceback.format_exc())
            return
        return result
    return wrap


def to_db_date(some_date):
    """
        converts a date to a date str for the database
    """
    dt = datetime.datetime.combine(some_date, datetime.datetime.min.time())
    return dt.strftime('%Y-%m-%d')


def to_date_str(some_date):
    """ we return something that is 'updatedable by dict'
        so we need to convert all dates into strings
    """
    if some_date:
        return some_date.strftime("%d/%m/%Y")


def to_datetime_str(some_datetime):
    """ we return something that is 'updatedable by dict'
        so we need to convert all datetimes into strings
    """
    if some_datetime:
        return some_datetime.strftime('%d/%m/%Y %H:%M:%S')


class Row(object):
    """ a simple wrapper to get us the fields we actually want out of a row
    """
    DEMOGRAPHICS_FIELDS = [
        'surname',
        'first_name',
        'date_of_birth',
        'sex',
        'ethnicity',
        'title',
        'date_of_birth',
        'hospital_number',
        'nhs_number'
    ]

    LAB_TEST_FIELDS = [
        'status',
        'test_code',
        'test_name',
        'datetime_ordered',
        'external_identifier',
    ]

    OBSERVATION_FIELDS = [
        'observation_number',
        'observation_name',
        'reference_range',
        'observation_value',
        'units',
        'observation_datetime',
        'last_updated',
    ]

    RESULT_FIELDS = LAB_TEST_FIELDS + OBSERVATION_FIELDS

    def __init__(self, db_row):
        self.db_row = db_row

    def get_or_fallback(self, primary_field, secondary_field):
        """ look at one field, if its empty, use a different field
        """
        # we use Cerner information if it exists, otherwise
        # we fall back to winpath demograhpics
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
        result["external_system"] = "RFH Demographics"
        return result

    # Results Fields

    # fields of the Lab Test
    def get_status(self):
        status_abbr = self.db_row.get("OBX_Status")

        if status_abbr == 'F':
            return lmodels.LabTest.COMPLETE
        else:
            return lmodels.LabTest.PENDING

    def get_test_code(self):
        return self.db_row.get('OBX_exam_code_ID')

    def get_test_name(self):
        return self.db_row.get("OBR_exam_code_Text")

    def get_external_identifier(self):
        return self.db_row.get("Result_ID")

    def get_datetime_ordered(self):
        return to_datetime_str(
            self.db_row.get(
                "Date_of_the_Observation", self.db_row.get("Request_Date")
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
        dt = self.db_row.get("Date_of_the_Observation")
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
        self.ip_address = settings.HOSPITAL_DB.get("ip_address")
        self.database = settings.HOSPITAL_DB.get("database")
        self.username = settings.HOSPITAL_DB.get("username")
        self.password = settings.HOSPITAL_DB.get("password")
        self.view = settings.HOSPITAL_DB.get("view")
        if not all([
            self.ip_address,
            self.database,
            self.username,
            self.password,
            self.view
        ]):
            raise ValueError(
                "You need to set proper credentials to use the prod api"
            )

    def execute_query(self, query, params=None):
        with pytds.connect(
            self.ip_address,
            self.database,
            self.username,
            self.password,
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchall()
        return result

    @property
    def demographics_query(self):
        return DEMOGRAPHICS_QUERY.format(view=self.view)

    @property
    def all_data_query(self):
        return ALL_DATA_QUERY.format(view=self.view)

    @property
    def all_data_query_for_lab_number(self):
        return ALL_DATA_QUERY_WITH_LAB_NUMBER.format(view=self.view)

    @property
    def all_data_query_for_lab_test_type(self):
        return ALL_DATA_QUERY_WITH_LAB_TEST_TYPE.format(view=self.view)

    def demographics(self, hospital_number):
        hospital_number = hospital_number.strip()
        try:
            rows = self.execute_query(
                self.demographics_query,
                params=dict(hospital_number=hospital_number)
            )
        except:
            logger = logging.getLogger('error_emailer')
            logger.error("unable to get demographics")
            logger = logging.getLogger('intrahospital_api')
            logger.error(traceback.format_exc())
            return
        if not len(rows):
            return

        return Row(rows[0]).get_demographics_dict()

    def raw_data(self, hospital_number, lab_number=None, test_type=None):
        """ not all data, I lied. Only the last year's
        """
        db_date = to_db_date(datetime.date.today() - datetime.timedelta(365))

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
                self.all_data_query,
                params=dict(hospital_number=hospital_number, since=db_date)
            )

    def cooked_data(self, hospital_number):
        raw_data = self.raw_data(hospital_number)
        return (Row(row).get_all_fields() for row in raw_data)

    def cast_rows_to_lab_test(self, rows):
        lab_number_to_observations = defaultdict(list)
        lab_number_to_lab_test = dict()

        for row in rows:
            lab_test_dict = row.get_lab_test_dict()
            lab_number = lab_test_dict["external_identifier"]
            lab_number_to_lab_test[lab_number] = lab_test_dict
            lab_number_to_observations[lab_number].append(
                row.get_observation_dict()
            )
        result = []

        for external_id, lab_test in lab_number_to_lab_test.items():
            lab_test = lab_number_to_lab_test[external_id]
            lab_test["observations"] = lab_number_to_observations[external_id]
            result.append(lab_test)
        return result

    def results_for_hospital_number(self, hospital_number):
        """
            returns all the results for a particular person

            aggregated into labtest: observations([])
        """

        raw_rows = self.raw_data(hospital_number)
        rows = (Row(raw_row) for raw_row in raw_rows)
        return self.cast_rows_to_lab_test(rows)
