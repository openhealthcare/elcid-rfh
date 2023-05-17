import datetime
from unittest.mock import patch
from django.test import override_settings
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


class FindPatientsFromMRNsTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def test_demographics_match(self):
        self.patient.demographics_set.update(
            hospital_number="123"
        )
        result = utils.find_patients_from_mrns(["123"])
        self.assertEqual(result["123"], self.patient)

    def test_demographics_zero_match(self):
        self.patient.demographics_set.update(
            hospital_number="123"
        )
        result = utils.find_patients_from_mrns(["0123"])
        self.assertEqual(result["0123"], self.patient)

    def test_ignore_empties(self):
        # we shouldn't have empty strings but if we
        # do we should not return them.
        self.patient.demographics_set.update(
            hospital_number=""
        )
        result = utils.find_patients_from_mrns([None])
        self.assertEqual(result, {})
        result = utils.find_patients_from_mrns([""])
        self.assertEqual(result, {})
        result = utils.find_patients_from_mrns(["000"])
        self.assertEqual(result, {})

    def test_merged_mrn_match(self):
        self.patient.demographics_set.update(
            hospital_number="234"
        )
        self.patient.mergedmrn_set.create(
            mrn="123"
        )
        result = utils.find_patients_from_mrns(["123"])
        self.assertEqual(result["123"], self.patient)

    def test_merged_mrn_zero_match(self):
        self.patient.demographics_set.update(
            hospital_number="234"
        )
        self.patient.mergedmrn_set.create(
            mrn="123"
        )
        result = utils.find_patients_from_mrns(["0123"])
        self.assertEqual(result["0123"], self.patient)

    def test_no_match(self):
        result = utils.find_patients_from_mrns(["123"])
        self.assertEqual(result, {})


@patch('elcid.utils.send_mail')
@patch('elcid.utils.logger')
@override_settings(
    OPAL_BRAND_NAME="Test brand name",
    DEFAULT_FROM_EMAIL="our@hospital_email",
    ADMINS=(('admin name', 'admin@admin.org',),)
)
class SendEmailTestCase(OpalTestCase):
    def test_calls_send_mail_and_logs(self, logger, send_mail):
        utils.send_email('test subject', 'test body')
        logger_calls = logger.info.call_args_list
        self.assertEqual(len(logger_calls), 2)
        self.assertEqual(
            logger_calls[0][0][0], "Sending email: test subject"
        )
        self.assertEqual(
            logger_calls[1][0][0], "Sent email: test subject"
        )
        send_mail.assert_called_once_with(
            "Test brand name: test subject",
            "test body",
            "our@hospital_email",
            ["admin@admin.org"],
            html_message=None
        )

    def test_with_html_message(self, logger, send_mail):
        utils.send_email('test subject', 'test body', html_message="<h1>test html</h1>")
        logger_calls = logger.info.call_args_list
        self.assertEqual(len(logger_calls), 2)
        self.assertEqual(
            logger_calls[0][0][0], "Sending email: test subject"
        )
        self.assertEqual(
            logger_calls[1][0][0], "Sent email: test subject"
        )
        send_mail.assert_called_once_with(
            "Test brand name: test subject",
            "test body",
            "our@hospital_email",
            ["admin@admin.org"],
            html_message="<h1>test html</h1>"
        )
