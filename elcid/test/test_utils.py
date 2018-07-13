import datetime
from mock import patch
from opal.core.test import OpalTestCase
from elcid import utils


class TestCase(OpalTestCase):

    def test_logging_method(self):
        class LoggingTest(object):
            @utils.method_logging
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
            first_call, "2018-02-03 10:21:00 starting LoggingTest.some_method"
        )
        self.assertEqual(
            second_call,
            "2018-02-03 10:22:00 finishing LoggingTest.some_method for \
2018-02-03 10:21:00"
        )
        self.assertEqual(
            result, "some_var"
        )
