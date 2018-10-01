import mock
from django.test import override_settings
from opal.core.test import OpalTestCase
from intrahospital_api import smoke_check


@override_settings(
    OPAL_BRAND_NAME="something",
    ADMINS=(("Wilma", "wilma@openhealthcare.org.uk",),)
)
@mock.patch("intrahospital_api.smoke_check.django_send_mail")
class CheckEmailTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        super(CheckEmailTestCase, self).setUp(*args, **kwargs)
        self.check_email = smoke_check.ChecksEmailMessage()

    def test_record_and_send(self, django_send_mail):
        self.check_email.record_problem(
            "some_problem", "problem with 1"
        )
        self.check_email.send()
        subject = django_send_mail.call_args[0][0]
        body = django_send_mail.call_args[0][1]
        from_name = django_send_mail.call_args[0][2]
        to = django_send_mail.call_args[0][3]
        html_message = django_send_mail.call_args[1]["html_message"]

        self.assertEqual(
            subject, "Batch Load Err: some_problem-1"
        )

        self.assertEqual(
            body, "some_problem-1\n\nproblem with 1"
        )

        self.assertEqual(
            to, ["wilma@openhealthcare.org.uk"]
        )

        self.assertEqual(
            from_name, "something"
        )

        self.assertEqual(
            html_message,  '<p>some_problem-1</p><br /><br /><p>problem with 1</p>'
        )

    def test_record_multiple_and_send(self, django_send_mail):
        self.check_email.record_problem(
            "some_problem", "problem with 1"
        )

        self.check_email.record_problem(

            "some_problem", "problem with 2"
        )

        self.check_email.record_problem(
            "some_problem", "other problem"
        )

        self.check_email.send()

        subject = django_send_mail.call_args[0][0]
        body = django_send_mail.call_args[0][1]
        html_message = django_send_mail.call_args[1]["html_message"]

        self.assertEqual(
            subject, "Batch Load Err: some_problem-1"
        )

        self.assertEqual(
            body, "some_problem-1\n\nproblem with 1"
        )

        self.assertEqual(
            html_message,  '<p>some_problem-1</p><br /><br /><p>problem with 1</p>'
        )

    def test_send_if_necessary(self, django_send_mail):
        pass


class LoadCheckTestCase(OpalTestCase):
    def test_check_load_time_success(self):
        pass

    def test_check_load_time(self):
        pass

    def test_amount_batch_runs_that_should_have_run_success(self):
        pass

    def test_amount_batch_runs_that_should_have_run_failed(self):
        pass


class CheckLoadsTestCase(OpalTestCase):
    def test_patients_should_have_been_added_success(self):
        pass

    def test_patients_should_have_been_added_failed(self):
        pass

    def test_amount_of_lab_tests_that_should_have_loaded_success(self):
        pass

    def test_amount_of_lab_tests_that_should_have_loaded_failed(self):
        pass