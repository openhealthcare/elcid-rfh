from intrahospital_api.base import api
import pytds
import re
from django.conf import settings

DEMOGRAPHICS_QUERY = "SELECT top(1) FROM {view} WHERE Patient_Number = \
'{hospital_number}' ORDER BY last_updated DESC;"


class ProdApi(api.BaseApi):
    def __init__(self):
        self.ip_address = settings.HOSPTIAL_DB["ip_address"]
        self.database = settings.HOSPTIAL_DB["database"]
        self.username = settings.HOSPTIAL_DB["username"]
        self.password = settings.HOSPTIAL_DB["password"]
        self.view = settings.HOSPTIAL_DB["view"]
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
        ))
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
