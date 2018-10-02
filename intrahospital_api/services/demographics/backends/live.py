from intrahospital_api.services.base import db
from intrahospital_api.constants import EXTERNAL_SYSTEM
from elcid.utils import timing
import logging

logger = logging.getLogger('intrahospital_api')
PATHOLOGY_VIEW = "Pathology_Result_view"

MAIN_DEMOGRAPHICS_VIEW = "VIEW_CRS_Patient_Masterfile"

MAIN_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;".format(
    view=MAIN_DEMOGRAPHICS_VIEW
)

# The pathology demographics query, looks at CERNER but falls back to WINPATH
# the view is limited to patients that are on WINPATH
PATHOLOGY_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;".format(view=PATHOLOGY_VIEW)


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


class PathologyDemographicsRow(db.Row):
    """ A simple wrapper to get us the fields we actually want out of a row
    """
    FIELD_MAPPINGS = dict(
        hospital_number="Patient_Number",
        nhs_number=("CRS_NHS_Number", "Patient_ID_External",),
        first_name=("CRS_Forename1", "Firstname",),
        surname=("CRS_Surname", "Surname",),
        date_of_birth="date_of_birth",
        sex="sex",
        ethnicity="ethnicity",
        title=("CRS_Title", "title",)
    )

    @property
    def date_of_birth(self):
        dob = self.get_or_fallback("CRS_DOB", "date_of_birth")
        if dob:
            return db.to_date_str(dob.date())

    @property
    def ethnicity(self):
        return ETHNICITY_MAPPING.get(self.db_row.get("CRS_Ethnic_Group"))

    @property
    def sex(self):
        sex_abbreviation = self.get_or_fallback("CRS_SEX", "SEX")

        if sex_abbreviation:
            if sex_abbreviation == "M":
                return "Male"
            else:
                return "Female"


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
        dob = self.db_row.get("DOB")
        if dob:
            return db.to_date_str(dob.date())

    @property
    def ethnicity(self):
        return ETHNICITY_MAPPING.get(self.db_row.get("ETHNIC_GROUP"))

    @property
    def sex(self):
        sex_abbreviation = self.db_row.get("SEX")

        if sex_abbreviation:
            if sex_abbreviation == "M":
                return "Male"
            else:
                return "Female"


class Api(object):
    """ Get a demographics dict for a patient
    """
    def __init__(self):
        self.connection = db.DBConnection()

    @timing
    def pathology_demographics_for_hospital_number(self, hospital_number):
        rows = self.connection.execute_query(
            PATHOLOGY_DEMOGRAPHICS_QUERY,
            hospital_number=hospital_number
        )
        return [PathologyDemographicsRow(i) for i in rows]

    @timing
    def main_demographics_for_hospital_number(self, hospital_number):
        rows = self.connection.execute_query(
            MAIN_DEMOGRAPHICS_QUERY,
            hospital_number=hospital_number
        )
        return [MainDemographicsRow(i) for i in rows]

    def demographics_for_hospital_number(self, hospital_number):
        hospital_number = hospital_number.strip()

        rows = self.main_demographics_for_hospital_number(hospital_number)

        if not rows:
            rows = self.pathology_demographics_for_hospital_number(
                hospital_number
            )

        if rows:
            result = rows[0].translate()
            result["external_system"] = EXTERNAL_SYSTEM
            return result





