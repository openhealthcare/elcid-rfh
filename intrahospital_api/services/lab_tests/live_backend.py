import datetime
import logging
from collections import defaultdict
from intrahospital_api.constants import EXTERNAL_SYSTEM
from intrahospital_api.services.base import db
from elcid.utils import timing
from lab import models as lmodels

VIEW = "Pathology_Result_view"

ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number ORDER BY last_updated DESC;".format(
    view=VIEW
)

ALL_DATA_QUERY_WITH_LAB_NUMBER = "SELECT * FROM {view} WHERE Result_ID = @lab_number \
ORDER BY last_updated DESC;".format(
    view=VIEW
)

ALL_DATA_QUERY_WITH_LAB_TEST_TYPE = "SELECT * FROM {view} WHERE Patient_Number = \
@hospital_number and OBR_exam_code_Text = @test_type ORDER BY last_updated \
DESC;".format(view=VIEW)

ALL_DATA_SINCE = "SELECT * FROM {view} WHERE last_updated > @since ORDER BY \
Patient_Number, last_updated DESC;".format(view=VIEW)

SUMMARY_RESULTS = "SELECT Patient_Number, Result_Value, Result_ID, last_updated from \
{view} WHERE Patient_Number = @hospital_number".format(view=VIEW)

QUICK_REVIEW = "SELECT Patient_Number, Result_ID, max(last_updated), count(*) \
from {view} group by Patient_Number, Result_ID".format(view=VIEW)


class Row(db.Row):
    """
    A simple wrapper to get us the fields we actually want out of a row
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

    @property
    def status(self):
        status_abbr = self.raw_data.get("OBX_Status")

        if status_abbr == 'F':
            return lmodels.LabTest.COMPLETE
        else:
            return lmodels.LabTest.PENDING

    @property
    def site(self):
        site = self.raw_data.get('Specimen_Site')
        if "^" in site and "-" in site:
            return site.split("^")[1].strip().split("-")[0].strip()
        return site

    @property
    def datetime_ordered(self):
        return db.to_datetime_str(
            self.raw_data.get(
                "Observation_date", self.raw_data.get("Request_Date")
            )
        )

    @property
    def observation_datetime(self):
        dt = self.raw_data.get("Observation_date")
        dt = dt or self.raw_data.get("Request_Date")
        return db.to_datetime_str(dt)

    @property
    def last_updated(self):
        return db.to_datetime_str(self.raw_data.get("last_updated"))

    def get_results_dict(self):
        result = {}
        result_keys = self.OBSERVATION_MAPPING.keys()
        result_keys = result_keys + self.LAB_TEST_MAPPING.keys()
        for field in result_keys:
            result[field] = getattr(self, field)

        return result

    def get_lab_test_dict(self):
        result = {}
        for field in self.LAB_TEST_MAPPING.keys():
            result[field] = getattr(self, field)
        return result

    def get_observation_dict(self):
        result = {}
        for field in self.OBSERVATION_MAPPING.keys():
            result[field] = getattr(self, field)
        return result

    def get_all_fields(self):
        result = {}
        for field in self.FIELD_MAPPINGS.keys():
            result[field] = getattr(self, field)
        return result


class SummaryRow(db.Row):
    FIELD_MAPPINGS = dict(
        observation_value="Result_Value",
        last_updated="last_updated",
        external_identifier="Result_ID",
        hospital_number="Patient_Number",
    )

    @property
    def last_updated(self):
        return db.to_datetime_str(self.raw_data.get("last_updated"))


class Backend(db.DatabaseBackend):

    def raw_lab_tests(self, hospital_number, test_type=None):
        if test_type:
            return self.connection.execute_query(
                ALL_DATA_QUERY_WITH_LAB_TEST_TYPE,
                hospital_number=hospital_number,
                test_type=test_type
            )
        else:
            return self.connection.execute_query(
                ALL_DATA_QUERY_FOR_HOSPITAL_NUMBER,
                hospital_number=hospital_number
            )

    def lab_tests_by_lab_test_number(self, lab_number):
            return self.connection.execute_query(
                ALL_DATA_QUERY_WITH_LAB_NUMBER,
                lab_number=lab_number
            )

    def get_summaries(self, *hospital_numbers):
        query_params = [
            dict(hospital_number=i) for i in hospital_numbers
        ]
        rows = self.connection.execute_query_multiple_times(
            SUMMARY_RESULTS, query_params
        )
        return self.group_summaries([SummaryRow(i) for i in rows])

    def group_summaries(self, summary_rows):
        result = defaultdict(lambda: defaultdict(list))
        for summary_row in summary_rows:
            hn = summary_row.hospital_number
            ln = summary_row.external_identifier
            result[hn][ln].append(
                (summary_row.observation_value, summary_row.last_updated,)
            )
        return result

    @timing
    def data_delta_query(self, since):
        all_rows = self.connection.execute_query(
            ALL_DATA_SINCE,
            since=since
        )
        return (Row(r) for r in all_rows)

    def lab_test_results_since(self, hospital_numbers, some_datetime):
        """
        Yields an iterator of dictionary

        The dictionary contains

            "demographics" : demographics, the first (ie the most recent)
            demographics result in the set.

            "lab_tests": all lab tests for the patient

        """
        all_rows = self.data_delta_query(some_datetime)
        hospital_number_to_rows = defaultdict(list)
        for row in all_rows:
            if row.hospital_number in hospital_numbers:
                hospital_number_to_rows[row.hospital_number].append(row)

        hospital_number_to_lab_tests = {}

        for hospital_number, rows in hospital_number_to_rows.items():
            lab_tests = self.cast_rows_to_lab_test(rows)
            hospital_number_to_lab_tests[hospital_number] = lab_tests

        return hospital_number_to_lab_tests

    def cooked_lab_tests(self, hospital_number):
        raw_lab_tests = self.raw_lab_tests(hospital_number)
        return (Row(row).get_all_fields() for row in raw_lab_tests)

    def cast_rows_to_lab_test(self, rows):
        """
        We cast multiple rows to lab tests.

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
        Returns all the results for a particular person

        Aggregated into labtest: observations([])
        """

        raw_rows = self.raw_lab_tests(hospital_number)
        rows = (Row(raw_row) for raw_row in raw_rows)
        return self.cast_rows_to_lab_test(rows)

    @timing
    def raw_summary_results(self, since):
        return self.connection.execute_query(
            SUMMARY_RESULTS,
            since=since
        )
