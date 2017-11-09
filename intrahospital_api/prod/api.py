import datetime
import pytds
import re
from intrahospital_api.base import api
from lab import models as lmodels
from django.conf import settings

DEMOGRAPHICS_QUERY = "SELECT top(1) FROM {view} WHERE Patient_Number = \
'{hospital_number}' ORDER BY last_updated DESC;"

ALL_DATA_QUERY = "SELECT * FROM {view} WHERE Patient_Number = \
'{hospital_number}' AND last_updated > '{since}' ORDER BY last_updated DESC;"


def to_db_date(some_date):
    """
        converts a date to a date str for the database
    """
    dt = datetime.combine(some_date, datetime.min.time())
    return dt.strftime('%Y-%m-%d')


class Row(object):
    """ a simple wrapper to get us the fields we actually want out of a row
    """
    DEMOGRAPHICS_FIELDS = [
        'surname',
        'first_name',
        'date_of_birth',
        'sex',
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

    def get_or_fallback(self, row, primary_field, secondary_field):
        """ look at one field, if its empty, use a different field
        """
        # we use Cerner information if it exists, otherwise
        # we fall back to winpath demograhpics
        # these are combined in the same table
        # so we fall back to a different
        # field name in the same row
        result = row.get(primary_field)

        if not result:
            result = row.get(secondary_field, "")

        return result

    # Demographics Fields
    def get_hospital_number(self):
        return self.db_row.get('Patient_Number', "CRS_NHS_Number")

    def get_nhs_number(self):
        return self.db_row.get('Patient_Number')

    def get_surname(self):
        return self.get_or_fallback(self.db_row, "CRS_Surname", "Surname")

    def get_first_name(self):
        return self.get_or_fallback(self.db_row, "CRS_Forename1", "Firstname")

    def get_sex(self):
        sex_abbreviation = self.get_or_fallback(self.db_row, "CRS_SEX", "SEX")

        if sex_abbreviation == "M":
            return "Male"
        else:
            return "Female"

    def get_date_of_birth(self):
        dob = self.get_or_fallback(self.db_row, "CRS_DOB", "date_of_birth")
        if dob:
            return dob.date()

    def get_title(self):
        return self.get_or_fallback(self.db_row, "CRS_Title", "title")

    def get_demographics_dict(self):
        result = {}
        for field in self.DEMOGRAPHICS_FIELDS:
            result[field] = self.getattr("get_{}".format(field))

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
            result[field] = self.getattr("get_{}".format(field))

        return result

    def get_all_fields(self):
        result = {}
        fields = self.DEMOGRAPHICS_FIELDS + self.RESULT_FIELDS
        for field in fields:
            result[field] = self.getattr("get_{}".format(field))

        return result


class ProdApi(api.BaseApi):
    def __init__(self):
        self.ip_address = settings.HOSPITAL_DB["ip_address"]
        self.database = settings.HOSPITAL_DB["database"]
        self.username = settings.HOSPITAL_DB["username"]
        self.password = settings.HOSPITAL_DB["password"]
        self.view = settings.HOSPITAL_DB["view"]
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

    def get_or_fallback(self, row, primary_field, secondary_field):
        """ look at one field, if its empty, use a different field
        """
        # we use Cerner information if it exists, otherwise
        # we fall back to winpath demograhpics
        # these are combined in the same table
        # so we fall back to a different
        # field name in the same row
        result = row.get(primary_field)

        if not result:
            result = row.get(secondary_field, "")

        return result

    def check_hospital_number(self, hospital_number):
        valid = re.match('^[\w- ]+$', str)
        if valid is not None:
            raise ValueError('unable to process {}'.format(hospital_number))

    def demographics(self, hospital_number):
        self.check_hospital_number(hospital_number)
        row = self.execute_query(DEMOGRAPHICS_QUERY.format(
            view=self.view, hospital_number=hospital_number
        ))[0]
        return self.cast_row_to_demographics_fields(row)

    def cast_row_to_demographics_fields(self, row):
        sex_abbreviation = self.get_or_fallback(row, "CRS_SEX", "SEX")

        if sex_abbreviation == "M":
            sex = "Male"
        else:
            sex = "Female"

        dob = self.get_or_fallback(row, "CRS_DOB", "date_of_birth")
        if dob:
            dob = dob.date()

        return dict(
            surname=self.get_or_fallback(row, "CRS_Surname", "Surname"),
            first_name=self.get_or_fallback(row, "CRS_Forename1", "Firstname"),
            sex=sex,
            title=self.get_or_fallback(row, "CRS_Title", "title"),
            date_of_birth=dob
        )

    def raw_data(self, hospital_number):
        """ not all data, I lied. Only the last year's
        """
        self.check_hospital_number(hospital_number)
        rows = self.execute_query(ALL_DATA_QUERY.format(
            view=self.view, hospital_number=hospital_number
        ))
        return rows

    def cooked_data(self, hospital_number):
        raw_data = self.raw_data(hospital_number)
        return (self.cook_data(row) for row in raw_data)

    def results(self, hospital_number):
        return {}
