import datetime
from mock import patch
from opal.core.test import OpalTestCase
from elcid import utils


class ModelMethodLoggingTestCase(OpalTestCase):

    def test_logging_method(self):
        class LoggingTest(object):
            id = 1

            @utils.model_method_logging
            def some_method(self):
                return "some_var"
        a = LoggingTest()
        with patch.object(utils.logger, "info") as info:
            with patch("elcid.utils.timezone.now") as now:
                first_call = datetime.datetime(2018, 2, 3, 10, 21)
                second_call = first_call + datetime.timedelta(minutes=1)
                now.side_effect = [first_call, second_call]
                result = a.some_method()
        first_call = info.call_args_list[0][0][0]
        second_call = info.call_args_list[1][0][0]
        self.assertEqual(
            first_call, "2018-02-03 10:21:00 starting LoggingTest.some_method \
(id 1)"
        )
        self.assertEqual(
            second_call,
            "2018-02-03 10:22:00 finishing LoggingTest.some_method (id 1) for \
2018-02-03 10:21:00"
        )
        self.assertEqual(
            result, "some_var"
        )


class WardSortTestCase(OpalTestCase):
    def test_ward_sort(self):
        wards = [
            "8 West",
            "PITU",
            "ICU 4 East",
            "9 East",
            "8 South",
            "Other",
            "9 North",
            "ICU 4 West",
            "12 West",
            "Outpatients",
        ]

        expected = [
            "8 South",
            "8 West",
            "9 East",
            "9 North",
            "12 West",
            "ICU 4 East",
            "ICU 4 West",
            "Outpatients",
            "PITU",
            "Other"
        ]
        self.assertEqual(
            expected, sorted(wards, key=utils.ward_sort_key)
        )

    def test_grouping(self):
        wards = [
            "8 West",
            "8 West",
            "9 East",
            "8 South",
            "9 North",
        ]

        expected = [
            "8 South",
            "8 West",
            "8 West",
            "9 East",
            "9 North",
        ]
        self.assertEqual(
            expected, sorted(wards, key=utils.ward_sort_key)
        )