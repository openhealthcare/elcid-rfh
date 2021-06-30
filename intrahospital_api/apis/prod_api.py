"""
API for production
"""
from collections import defaultdict
import datetime
from functools import wraps
import itertools
import json
import time

from django.conf import settings
from django.utils import timezone
import pytds
from pytds.tds import OperationalError

from elcid.models import (
    Demographics, ContactInformation, NextOfKinDetails, GPDetails,
    MasterFileMeta
)
from elcid.utils import timing
from intrahospital_api.apis import base_api
from intrahospital_api import logger
from intrahospital_api.constants import EXTERNAL_SYSTEM

# if we fail in a query, the amount of seconds we wait before retrying
RETRY_DELAY = 30

PATIENT_MASTERFILE_VIEW = "VIEW_CRS_Patient_Masterfile"

PATHOLOGY_DEMOGRAPHICS_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY date_inserted DESC;"

PATIENT_MASTERFILE_QUERY = "SELECT top(1) * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;"

PATIENT_MASTER_FILE_SINCE_QUERY = """
SELECT * FROM VIEW_CRS_Patient_Masterfile WHERE
last_updated > @last_updated OR
insert_date > @last_updated
"""

ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY date_inserted DESC;"

ALL_DATA_QUERY_WITH_LAB_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number and Result_ID = @lab_number ORDER BY date_inserted DESC;"


ALL_DATA_QUERY_WITH_LAB_NUMBER = "SELECT * FROM VIEW_ElCid_Radiology_Results WHERE Result_ID = @lab_number ORDER BY date_inserted DESC;"

ALL_DATA_QUERY_WITH_LAB_TEST_TYPE = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number AND OBR_exam_code_Text = @test_type ORDER BY date_inserted DESC;"

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
    MODIFIED_DEMOGRAPHICS_FIELDS = [
        "date_of_birth",
        "sex",
        "ethnicity",
        "date_of_death",
        "death_indicator"
    ]

    DIRECT_UPSTREAM_FIELDS_TO_ELCID_FIELDS = {
        'hospital_number': 'PATIENT_NUMBER',
        'nhs_number'     : 'NHS_NUMBER',
        'first_name'     : 'FORENAME1',
        'middle_name'    : 'FORENAME2',
        'surname'        : 'SURNAME',
        'title'          : 'TITLE',
        'religion'       : 'RELIGION',
        'marital_status' : 'MARITAL_STATUS',
        'nationality'    : 'NATIONALITY',
        'main_language'    : 'MAIN_LANGUAGE',
    }

    def __init__(self, db_row):
        self.db_row = db_row

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

    def get_date_of_death(self):
        date_of_death = self.db_row.get('DATE_OF_DEATH')
        # Sometimes the upstream database will return '' which raises a strptime error
        if date_of_death:
            return date_of_death

    def get_death_indicator(self):
        alive = self.db_row.get("DEATH_FLAG") == 'ALIVE'
        return not alive

    def get_demographics_dict(self):
        result = {}
        for field in self.MODIFIED_DEMOGRAPHICS_FIELDS:
            result[field] = getattr(self, "get_{}".format(field))()

        for field in self.DIRECT_UPSTREAM_FIELDS_TO_ELCID_FIELDS:
            result[field] = self.db_row.get(
                self.DIRECT_UPSTREAM_FIELDS_TO_ELCID_FIELDS[field]
            )

        return result

def get_contact_information(row):
    mapping = {
        "address_line_1": "ADDRESS_LINE1",
        "address_line_2": "ADDRESS_LINE2",
        "address_line_3": "ADDRESS_LINE3",
        "address_line_4": "ADDRESS_LINE4",
        "postcode": "POSTCODE",
        "home_telephone": "HOME_TELEPHONE",
        "work_telephone": "WORK_TELEPHONE",
        "mobile_telephone": "MOBILE_TELEPHONE",
        "email": "EMAIL"
    }
    result = {}
    for our_field, their_field in mapping.items():
        result[our_field] = row[their_field]

    result["external_system"] = EXTERNAL_SYSTEM
    return result


def get_next_of_kin_details(row):
    mapping = {
        "nok_type": "NOK_TYPE",
        "surname": "NOK_SURNAME",
        "forename_1": "NOK_FORENAME1",
        "forename_2": "NOK_FORENAME2",
        "relationship": "NOK_relationship",
        "address_1": "NOK_address1",
        "address_2": "NOK_address2",
        "address_3": "NOK_address3",
        "address_4": "NOK_address4",
        "postcode": "NOK_Postcode",
        "home_telephone": "nok_home_telephone",
        "work_telephone": "nok_work_telephone",
    }
    result = {}
    for our_field, their_field in mapping.items():
        result[our_field] = row[their_field]

    result["external_system"] = EXTERNAL_SYSTEM
    return result

def get_gp_details(row):
    mapping = {
        "crs_gp_masterfile_id": "CRS_GP_MASTERFILE_ID",
        "national_code": "GP_NATIONAL_CODE",
        "practice_code": "GP_PRACTICE_CODE",
        "title": "gp_title",
        "initials": "GP_INITIALS",
        "surname": "GP_SURNAME",
        "address_1": "GP_ADDRESS1",
        "address_2": "GP_ADDRESS2",
        "address_3": "GP_ADDRESS3",
        "address_4": "GP_ADDRESS4",
        "postcode": "GP_POSTCODE",
        "telephone": "GP_TELEPHONE"
    }
    result = {}
    for our_field, their_field in mapping.items():
        result[our_field] = row[their_field]

    result["external_system"] = EXTERNAL_SYSTEM
    return result


def get_master_file_meta(row):
    mapping = {
        "insert_date": "INSERT_DATE",
        "last_updated": "LAST_UPDATED",
        "merged": "MERGED",
        "merge_comments": "MERGE_COMMENTS",
        "active_inactive": "ACTIVE_INACTIVE",
    }
    result = {}
    for our_field, their_field in mapping.items():
        result[our_field] = row[their_field]

    if result["last_updated"]:
        result["last_updated"] = timezone.make_aware(
            result["last_updated"]
        )

    if result["insert_date"]:
        result["insert_date"] = timezone.make_aware(
            result["insert_date"]
        )

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
        'encounter_consultant_name',
        'encounter_location_code',
        'encounter_location_name',
        'accession_number',
    ]

    OBSERVATION_FIELDS = [
        'last_updated',
        'observation_datetime',
        'observation_name',
        'observation_number',
        'observation_value',
        'reported_datetime',
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
            return "complete"
        else:
            return "pending"

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

    def get_encounter_consultant_name(self):
        return self.db_row.get("Encounter_Consultant_Name")

    def get_encounter_location_code(self):
        return self.db_row.get("Encounter_Location_Code")

    def get_encounter_location_name(self):
        return self.db_row.get("Encounter_Location_Name")

    def get_accession_number(self):
        return self.db_row.get("Accession_number")

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

    def get_reported_datetime(self):
        return to_datetime_str(self.db_row.get('Reported_date'))

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
        self.warehouse_settings = settings.WAREHOUSE_DB
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

    def execute_hospital_insert(self, insert, params=None):
        """
        Given an INSERT query, and optional PARAMS, execute and commit
        an insert on the upstream hospital database.
        """
        with pytds.connect(
            self.hospital_settings["ip_address"],
            self.hospital_settings["database"],
            self.hospital_settings["username"],
            self.hospital_settings["password"],
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                logger.info(
                    "Running upstream insert {} {}".format(insert, params)
                )
                cur.execute(insert, params)
                conn.commit()

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
                result = cur.fetchall()
        logger.debug(result)
        return result

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
                result = cur.fetchall()
        logger.debug(result)
        return result

    def execute_warehouse_query(self, query, params=None):
        with pytds.connect(
            self.warehouse_settings["ip_address"],
            self.warehouse_settings["database"],
            self.warehouse_settings["username"],
            self.warehouse_settings["password"],
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                logger.info(
                    "Running warehouse query {} {}".format(query, params)
                )
                cur.execute(query, params)
                result = cur.fetchall()
        logger.debug(result)
        return result

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
    def patient_masterfile_query(self):
        return PATIENT_MASTERFILE_QUERY.format(view=PATIENT_MASTERFILE_VIEW)

    def demographics(self, hospital_number):
        hospital_number = hospital_number.strip()
        demographics_result = None

        master_file_result = self.patient_masterfile(hospital_number)

        if master_file_result:
            demographics_result = master_file_result[Demographics.get_api_name()]

        if not demographics_result:
            demographics_result = self.pathology_demographics(hospital_number)

        if demographics_result:
            demographics_result["external_system"] = EXTERNAL_SYSTEM
            return demographics_result

    @timing
    def patient_masterfile_since(self, last_updated):
        """
        Returns the results in VIEW_CRS_Patient_Masterfile
        since a certain datetime.
        """
        rows = list(self.execute_hospital_query(
            PATIENT_MASTER_FILE_SINCE_QUERY, params={
                "last_updated": last_updated
            }
        ))
        result = []
        for row in rows:
            demographics = MainDemographicsRow(row).get_demographics_dict()
            result.append({
                Demographics.get_api_name(): demographics,
                ContactInformation.get_api_name(): get_contact_information(row),
                NextOfKinDetails.get_api_name(): get_next_of_kin_details(row),
                GPDetails.get_api_name(): get_gp_details(row),
                MasterFileMeta.get_api_name(): get_master_file_meta(row),
            })
        return result

    @timing
    @db_retry
    def patient_masterfile(self, hospital_number):
        rows = list(self.execute_hospital_query(
            self.patient_masterfile_query,
            params=dict(hospital_number=hospital_number)
        ))
        if not len(rows):
            return

        return {
            Demographics.get_api_name(): MainDemographicsRow(rows[0]).get_demographics_dict(),
            ContactInformation.get_api_name(): get_contact_information(rows[0]),
            NextOfKinDetails.get_api_name(): get_next_of_kin_details(rows[0]),
            GPDetails.get_api_name(): get_gp_details(rows[0]),
            MasterFileMeta.get_api_name(): get_master_file_meta(rows[0]),
        }

    @timing
    @db_retry
    def pathology_demographics(self, hn):
        hospital_number = hn
        rows = list(self.execute_trust_query(
            self.pathology_demographics_query,
            params=dict(hospital_number=hospital_number)
        ))
        if not len(rows):
            # If the hn begins with leading 0(s)
            # the data is sometimes empty in the CRS_* fields.
            # So if we cannot find rows with 0 prefixes
            # remove the prefix.
            if not hospital_number.startswith("0"):
                return
            hospital_number = hospital_number.lstrip('0')

            # some hns are just 0s, if we've stripped the hn
            # away don't query again.
            if not hospital_number:
                return
            rows = list(self.execute_trust_query(
                self.pathology_demographics_query,
                params=dict(hospital_number=hospital_number)
            ))
            if not len(rows):
                return
            # If we've stripped off the leading 0, restore it.
            if not hn == hospital_number:
                for row in rows:
                    row["Patient_Number"] = hn
        return PathologyRow(rows[0]).get_demographics_dict()

    def raw_data(self, hospital_number, lab_number=None, test_type=None):
        if lab_number:
            return self.execute_trust_query(
                self.all_data_query_for_lab_number,
                params=dict(
                    hospital_number=hospital_number,
                    lab_number=lab_number
                )
            )
        if test_type:
            return self.execute_trust_query(
                self.all_data_query_for_lab_test_type,
                params=dict(
                    hospital_number=hospital_number,
                    test_type=test_type
                )
            )
        else:
            return self.execute_trust_query(
                self.all_data_for_hospital_number_query,
                params=dict(hospital_number=hospital_number)
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
        """
        Returns a list of instances like
        {
         "demographics" : demographics, the first (ie the most recent) demographics result in the set.
         "lab_tests": all lab tests for the patient
        }
        """
        all_rows = self.data_delta_query(some_datetime)

        hospital_number_to_rows = defaultdict(list)

        for row in all_rows:
            hospital_number_to_rows[row.get_hospital_number()].append(row)

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
