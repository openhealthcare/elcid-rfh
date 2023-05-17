# do they view the trend graphs in the detail page and in the list page
# also do they see the UpstreamBloodCulturePanel
VIEW_LAB_TEST_TRENDS = "view_lab_test_trends"

# do they see the Lab Tests Patient Detail View
VIEW_LAB_TESTS_IN_DETAIL = "view_lab_tests_in_detail"

# can they view the reconcile demographics patient list
UPDATE_DEMOGRAPHICS = "update_demographics"

INTRAHOSPITAL_ROLES = set([
    VIEW_LAB_TEST_TRENDS,
    VIEW_LAB_TESTS_IN_DETAIL,
    UPDATE_DEMOGRAPHICS,
])

SEND_TO_EPR = "send_to_epr"
EXTERNAL_SYSTEM = "RFH Database"

MERGE_LOAD_MINUTES = "MERGE_LOAD_MINUTES"
TOTAL_MERGE_COUNT = "TOTAL_MERGE_COUNT"
