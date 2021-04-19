"""
Unittests for plugins.covid.calculator
"""
import datetime
from unittest import mock
from opal.core.test import OpalTestCase

from plugins.covid import calculator


class DayTestCase(OpalTestCase):

    def test_init(self):
        day = calculator.Day()

        self.assertEqual(0, day.tests_ordered)
        self.assertEqual(0, day.tests_resulted)
        self.assertEqual(0, day.patients_positive)
        self.assertEqual(0, day.patients_resulted)
        self.assertEqual(0, day.deaths)


class GetWeekTestCase(OpalTestCase):
    def test_on_monday(self):
        some_dt = datetime.date(2021, 3, 29)
        self.assertEqual(
            calculator.get_week(some_dt),
            (
                datetime.date(2021, 3, 29),
                datetime.date(2021, 4, 4)
            )
        )

    def test_on_sunday(self):
        some_dt = datetime.date(2021, 4, 4)
        self.assertEqual(
            calculator.get_week(some_dt),
            (
                datetime.date(2021, 3, 29),
                datetime.date(2021, 4, 4)
            )
        )

    def test_in_between(self):
        some_dt = datetime.date(2021, 4, 1)
        self.assertEqual(
            calculator.get_week(some_dt),
            (
                datetime.date(2021, 3, 29),
                datetime.date(2021, 4, 4)
            )
        )


@mock.patch("plugins.covid.calculator.datetime")
class GetWeekRangeTestCase(OpalTestCase):
    def test_from_monday(self, dt):
        dt.timedelta = datetime.timedelta
        dt.date.today.return_value = datetime.date(2021, 3, 30)
        result = calculator.get_week_range(
            datetime.date(2021, 3, 22)
        )
        expected = [
            (datetime.date(2021, 3, 22),  datetime.date(2021, 3, 28),),
            (datetime.date(2021, 3, 29),  datetime.date(2021, 4, 4),),
        ]
        self.assertEqual(result, expected)

    def test_same_day(self, dt):
        dt.timedelta = datetime.timedelta
        dt.date.today.return_value = datetime.date(2021, 3, 30)
        result = calculator.get_week_range(
            datetime.date(2021, 3, 30)
        )
        expected = [
            (datetime.date(2021, 3, 29),  datetime.date(2021, 4, 4),),
        ]
        self.assertEqual(result, expected)