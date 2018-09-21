import datetime
import mock
from pytds.tds import OperationalError
from opal.core.test import OpalTestCase
from intrahospital_api.base import db


@mock.patch("intrahospital_api.base.db.time")
class DbRetryTestCase(OpalTestCase):
    def test_retrys(self, time):
        m = mock.MagicMock(
            side_effect=[OperationalError('boom'), "response"]
        )
        m.__name__ = "some_mock"

        with mock.patch.object(db.logger, "info") as info:
            response = db.db_retry(m)()

        self.assertEqual(
            response, "response"
        )
        time.sleep.assert_called_once_with(30)
        info.assert_called_once_with(
            'some_mock: failed with boom, retrying in 30s'
        )

    def tests_works_as_normal(self, time):
        m = mock.MagicMock()
        m.return_value = "response"
        m.__name__ = "some_mock"

        with mock.patch.object(db.logger, "info") as info:
            response = db.db_retry(m)()

        self.assertEqual(
            response, "response"
        )
        self.assertFalse(time.sleep.called)
        self.assertFalse(info.called)

    def tests_reraises(self, time):
        m = mock.MagicMock(
            side_effect=OperationalError('boom')
        )
        m.__name__ = "some_mock"

        with mock.patch.object(db.logger, "info") as info:
            with self.assertRaises(OperationalError):
                db.db_retry(m)()

        time.sleep.assert_called_once_with(30)
        info.assert_called_once_with(
            'some_mock: failed with boom, retrying in 30s'
        )



class ToDateStrTestCase(OpalTestCase):
    def test_to_date_str(self):
        dt = datetime.datetime(2018, 8, 13, 22, 30, 24)
        self.assertEqual(
            db.to_date_str(dt),
            "13/08/2018"
        )


class ToDatetimeStrTestCase(OpalTestCase):
    def test_to_datetime_str(self):
        dt = datetime.datetime(2018, 8, 13, 22, 30, 24)
        self.assertEqual(
            db.to_datetime_str(dt),
            '13/08/2018 22:30:24'
        )


class TestRow(db.Row):
    @property
    def something(self):
        return "interesting"


class RowTestCase(OpalTestCase):
    def test_test_get_or_fallback(self):
        self.assertEqual(
            TestRow(dict(a=1, b=2)).get_or_fallback("a", "b"),
            1
        )

        self.assertEqual(
            TestRow(dict(a=None, b=2)).get_or_fallback("a", "b"),
            2
        )

    def test_get_item_vanilla(self):
        test_row = TestRow(dict(a="1"))
        test_row.FIELD_MAPPINGS = dict(b="a")
        self.assertEqual(
            test_row["b"], "1"
        )

    def test_get_item_list_first(self):
        """
        The first item should take priority over the second
        """
        test_row = TestRow(dict(a="1", c="2"))
        test_row.FIELD_MAPPINGS = dict(b=["c", "a"])
        self.assertEqual(
            test_row["b"], "2"
        )

    def test_get_item_list_second(self):
        test_row = TestRow(dict(a="1", c=None))
        test_row.FIELD_MAPPINGS = dict(b=["c", "a"])
        self.assertEqual(
            test_row["b"], "1"
        )

    def test_get_item_tuple(self):
        test_row = TestRow(dict(a="1", c=None))
        test_row.FIELD_MAPPINGS = dict(b=("c", "a",))
        self.assertEqual(
            test_row["b"], "1"
        )

    def test_get_item_property(self):
        test_row = TestRow(dict())
        test_row.FIELD_MAPPINGS = dict(looking="something")
        self.assertEqual(test_row["looking"], "interesting")
