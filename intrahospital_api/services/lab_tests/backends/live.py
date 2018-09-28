import datetime
import logging
from collections import defaultdict
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api.services.base import db
from elcid.utils import timing
from lab import models as lmodels

VIEW = "Pathology_Result_view"

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

LAB_TESTS_COUNT_FOR_HOSPITAL_NUMBER = "SELECT Count(DISTINCT Result_ID) FROM Pathology_Result_view WHERE \
Patient_Number=@hospital_number AND last_updated >= @since GROUP BY Patient_Number".format(view=VIEW)


class Row(db.Row):
    """ a simple wrapper to get us the fields we actually want out of a row
    """
    DEMOGRAPHICS_MAPPING = dict(
        hospital_number="Patient_Number",
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

    FIELD_MAPPINGS = dict(
        OBSERVATION_MAPPING.items() + LAB_TEST_MAPPING.items() + DEMOGRAPHICS_MAPPING.items()
    )

    def __init__(self, db_row):
        self.db_row = db_row

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
        for field in self.LAB_TEST_MAPPING.keys():
            result[field] = self[field]
        return result

    def get_observation_dict(self):
        result = {}
        for field in self.OBSERVATION_MAPPING.keys():
            result[field] = self[field]
        return result

    def get_all_fields(self):
        result = {}
        for field in self.FIELD_MAPPINGS.keys():
            result[field] = self[field]
        return result


class Api(object):
    def __init__(self):
        self.connection = db.DBConnection()

    def raw_lab_tests(
            self,
            hospital_number,
            lab_number=None,
            test_type=None,
            db_date=None
        ):
        """ if not db date, just get last years data
        """
        if db_date is None:
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


    def lab_test_results_since_2(self, hospital_numbers, some_datetime):
        hospital_number_to_rows = defaultdict(list)

        for hospital_number in hospital_numbers:
            hospital_number_to_rows[hospital_number].append(
                self.raw_lab_tests(hospital_number, some_datetime)
            )

        hospital_number_to_lab_tests = {}

        for hospital_number, rows in hospital_number_to_rows.items():
            lab_tests = self.cast_rows_to_lab_test(rows)
            hospital_number_to_lab_tests[hospital_number] = lab_tests

        return hospital_number_to_lab_tests


    @timing
    def data_delta_query(self, since):
        all_rows = self.connection.execute_query(
            ALL_DATA_SINCE,
            since=since
        )
        return (Row(r) for r in all_rows)

    def lab_test_results_since(self, hospital_numbers, some_datetime):
        """ yields an iterator of dictionary

            the dictionary contains

            "demographics" : demographics, the first (ie the most recent)
            demographics result in the set.

            "lab_tests": all lab tests for the patient

        """
        all_rows = self.data_delta_query(some_datetime)
        hospital_number_to_rows = defaultdict(list)

        for row in all_rows:
            if row["hospital_number"] in hospital_numbers:
                hospital_number_to_rows[row["hospital_number"]].append(row)

        hospital_number_to_lab_tests = {}

        for hospital_number, rows in hospital_number_to_rows.items():
            lab_tests = self.cast_rows_to_lab_test(rows)
            hospital_number_to_lab_tests[hospital_number] = lab_tests

        return hospital_number_to_lab_tests

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

    def lab_test_count_for_hospital_number(self, hospital_number, since):
        rows = list(self.connection.execute_query(
            LAB_TESTS_COUNT_FOR_HOSPITAL_NUMBER,
            hospital_number=hospital_number,
            since=since
        ))        
        if len(rows):
            return rows[0][0]
        else:
            return 0

    @timing
    def lab_tests_for_hospital_number(self, hospital_number):
        """
            returns all the results for a particular person

            aggregated into labtest: observations([])
        """

        raw_rows = self.raw_lab_tests(hospital_number)
        rows = (Row(raw_row) for raw_row in raw_rows)
        return self.cast_rows_to_lab_test(rows)
