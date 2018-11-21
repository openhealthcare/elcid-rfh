from intrahospital_api.services.base import db
from intrahospital_api.constants import EXTERNAL_SYSTEM
from elcid.utils import timing

RESULTS_VIEW = "Pathology_Result_view"
MAIN_DEMOGRAPHICS_VIEW = "VIEW_CRS_Patient_Masterfile"


PATHOLOGY_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;".format(view=RESULTS_VIEW)

MAIN_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;".format(
    view=MAIN_DEMOGRAPHICS_VIEW
)


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
        title="TITLE",
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
        dob = self._get_or_fallback("CRS_DOB", "date_of_birth")
        if dob:
            return db.to_date_str(dob.date())

    @property
    def ethnicity(self):
        return ETHNICITY_MAPPING.get(self.raw_data.get("CRS_Ethnic_Group"))

    @property
    def sex(self):
        sex_abbreviation = self._get_or_fallback("CRS_SEX", "SEX")

        if sex_abbreviation == "M":
            return "Male"
        else:
            return "Female"

    def get_demographics_dict(self):
        result = {}
        for field in self.FIELD_MAPPINGS.keys():
            result[field] = getattr(self, field)
        return result


class Api(db.DBConnection):
    @timing
    @db.db_retry
    def main_demographics(self, hospital_number):
        rows = list(self.execute_query(
            MAIN_DEMOGRAPHICS_QUERY,
            hospital_number=hospital_number
        ))
        if not len(rows):
            return
        return MainDemographicsRow(rows[0]).get_demographics_dict()

    @timing
    @db.db_retry
    def pathology_demographics(self, hospital_number):
        rows = list(self.execute_query(
            PATHOLOGY_DEMOGRAPHICS_QUERY,
            hospital_number=hospital_number
        ))
        if not len(rows):
            return

        return PathologyRow(rows[0]).get_demographics_dict()

    @timing
    def demographics_for_hospital_number(self, hospital_number):
        hospital_number = hospital_number.strip()

        demographics_result = self.main_demographics(hospital_number)

        if not demographics_result:
            demographics_result = self.pathology_demographics(hospital_number)

        if demographics_result:
            demographics_result["external_system"] = EXTERNAL_SYSTEM
            return demographics_result
