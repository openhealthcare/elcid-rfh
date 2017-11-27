import datetime
import logging
import pytds
import re
from intrahospital_api.apis import base_api
from lab import models as lmodels
from django.conf import settings


DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
'{hospital_number}' ORDER BY last_updated DESC;"

ALL_DATA_QUERY = "SELECT * FROM {view} WHERE Patient_Number = \
'{hospital_number}' AND last_updated > '{since}' ORDER BY last_updated DESC;"

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


def to_db_date(some_date):
    """
        converts a date to a date str for the database
    """
    dt = datetime.datetime.combine(some_date, datetime.datetime.min.time())
    return dt.strftime('%Y-%m-%d')


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

    RESULT_FIELDS = [
        'reference_range',
        'status',
        'test_code',
        'test_name',
        'observation_value',
        'units',
        'external_identifier'
    ]

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
        return self.db_row.get('Patient_Number')

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
            return dob.date()

    def get_title(self):
        return self.get_or_fallback("CRS_Title", "title")

    def get_demographics_dict(self):
        result = {}
        for field in self.DEMOGRAPHICS_FIELDS:
            result[field] = getattr(self, "get_{}".format(field))()
        result["external_system"] = "RFH Demographics"
        return result

    # Results Fields
    def get_reference_range(self):
        return self.db_row.get("Result_Range")

    def get_status(self):
        status_abbr = self.db_row.get("OBX_Status")

        if status_abbr == 'F':
            return lmodels.LabTest.COMPLETE
        else:
            return lmodels.LabTest.PENDING

    def get_test_code(self):
        return self.db_row.get('OBX_exam_code_ID')

    def get_test_name(self):
        return self.db_row.get('OBX_exam_code_Text')

    def get_observation_value(self):
        return self.db_row.get('Result_Value')

    def get_units(self):
        return self.db_row.get("Result_Units")

    def get_external_identifier(self):
        return self.db_row.get("OBX_id")

    def get_results_dict(self):
        result = {}
        for field in self.RESULT_FIELDS:
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

    def execute_query(self, query):
        with pytds.connect(
            self.ip_address,
            self.database,
            self.username,
            self.password,
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()
        return result

    def check_hospital_number(self, hospital_number):
        """ hospital numbers hould be alpha numeric, space or -
            nothing else
        """

        valid = re.match('^[\w\-\s]+$', hospital_number)

        # -- is an sql comment, lets remove those
        if valid is None or "--" in hospital_number:
            err = "flawed hosital number {} passed to the intrahospital api"
            err = err.format(hospital_number)
            logger = logging.getLogger('intrahospital_api')
            logger.error(err)
            raise ValueError(err)

    def demographics(self, hospital_number):
        hospital_number = hospital_number.strip()
        try:
            self.check_hospital_number(hospital_number)
        except ValueError:
            return
        try:
            rows = self.execute_query(DEMOGRAPHICS_QUERY.format(
                view=self.view, hospital_number=hospital_number
            ))
        except:
            logger = logging.getLogger('error_emailer')
            logger.error("unable to get demographics")
            return
        if not len(rows):
            return

        return Row(rows[0]).get_demographics_dict()

    def raw_data(self, hospital_number):
        """ not all data, I lied. Only the last year's
        """
        self.check_hospital_number(hospital_number)
        db_date = to_db_date(datetime.date.today() - datetime.timedelta(365))
        rows = self.execute_query(ALL_DATA_QUERY.format(
            view=self.view, hospital_number=hospital_number, since=db_date
        ))
        return rows

    def cooked_data(self, hospital_number):
        raw_data = self.raw_data(hospital_number)
        return (Row(row).get_all_fields() for row in raw_data)

    def results(self, hospital_number):
        """
            will be implemented in a later release
        """
        return {}
