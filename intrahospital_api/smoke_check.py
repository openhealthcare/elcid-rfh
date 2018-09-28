"""
Smoke checks to make sure that we are happy with the
upstream loads
"""
import datetime
from collections import Counter
from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from lab import models as lab_models
from intrahospital_api import models
from intrahospital_api.services.lab_tests import service as lab_test_service
from intrahospital_api.services.demographics import service as demographics_service

from intrahospital_api import logger


# the mimum amount expected to be loaded by x
MIN_DAILY_EXPECTED_AMOUNT = 1

# the max time that any load should be taking in seconds
MAX_LOAD_TIME = 600


def min_datetime():
    return datetime.datetime.combine(datetime.date.today(), datetime.time.min)


def get_todays_loads(qs):
    return qs.filter(
        start__gte=min_datetime()
    )


class ChecksEmailMessage(object):
    """
    An email wrapper that allows you to add a bunch of issues
    """
    def __init__(self):
        self.method_issues = []
        self.text = []

    def record_problem(self, method_name, body):
        self.method_issues.append(method_name)
        self.text.append(body)

    def get_html(self, some_list):
        return "".join("<p>{}</p>".format(i) for i in some_list)

    def get_text(self, some_list):
        return "\n".join(some_list)

    def get_method_issues(self):
        counter = Counter(self.method_issues)
        return ["{}-{}".format(i, v) for i, v in counter.items()]

    def get_subject(self):
        subject = "Batch Load Err: {}".format(", ".join(self.get_method_issues()))
        return subject[:75]

    def send(self):
        subject = self.get_subject()
        body = "{}\n\n{}".format(
            self.get_text(self.get_method_issues()),
            self.get_text(self.text)
        )

        html_body = "{}<br /><br />{}".format(
            self.get_html(self.get_method_issues()),
            self.get_html(self.text)
        )

        for admin in settings.ADMINS:
            django_send_mail(
                subject,
                body,
                admin[1],
                settings.OPAL_BRAND_NAME,
                html_message=html_body
            )

    def send_if_necessary(self):
        if self.text:
            self.send()


class LoadCheck(object):
    """

    """
    def __init__(
        self,
        email,
        name,
        qs,
        min_daily_expected_amount=MIN_DAILY_EXPECTED_AMOUNT,
        max_load_time=MAX_LOAD_TIME,
    ):
        self.email = email
        self.name = name
        self.qs = get_todays_loads(qs)
        self.max_load_time = max_load_time
        self.min_daily_expected_amount = min_daily_expected_amount

    def check_load_time(self):
        """
        A qs should not be more long running that { amount }

        e.g. no initial patient load should last longer than 10 mins

        no lab test batch load should last longer than { amount }
        """

        running = self.qs.filter(state=models.PatientLoad.RUNNING)
        now = datetime.datetime.now()

        for runner in running:
            running_time = (now - runner).seconds
            err_body = "{} has been running for {}, should be finished in {}"
            if running_time < self.max_load_time:
                self.email.record_problem(
                    "Long running load",
                    err_body.format(
                        runner, running_time, self.min_daily_expected_amount
                    )
                )

        succeeded = self.qs.filter(state=models.PatientLoad.SUCCESS)

        for success in succeeded:
            running_time = (success.end - success.start).seconds
            if running_time < self.max_load_time:
                err_body = "{} has been succeeded in {}, should be finished in {}"
                self.email.record_problem(
                    "Load took too long",
                    err_body.format(
                        success, running_time, self.min_daily_expected_amount
                    )
                )

    def amount_of_batch_runs_that_should_have_run(self):
        """
        We expect at least {amount} {name} runs to run on a daily basis
        """

        if self.qs.count() < self.min_daily_expected_amount:
            self.email.record_problem(
                "{} batch amount".format(self.name),
                "There were only {} run for {} patient loads".format(
                    self.min_daily_expected_amount, self.name
                )
            )

    def check(self):
        self.check_load_time()
        self.amount_of_batch_runs_that_should_have_run()
        return self.email


def get_todays_ipl():
    return get_todays_loads(models.InitialPatientLoad.objects.all())


def patients_should_have_been_added(email):
    """
    We expect at least one patient to have been added every day
    """
    todays_ipls = get_todays_ipl()
    if not todays_ipls.exists():
        email.record_problem(
            "patients_should_have_been_added",
            "No initial patient loads have happened today"
        )
    return email


def amount_of_lab_tests_that_should_have_loaded(email):
    """
    At least some lab tests not including Initial Patient Loads
    should have loaded.
    """
    lab_tests = lab_models.LabTest.objects.filter(
        created__gt=min_datetime()
    ).filter(
        lab_test_type__istartswith="upstream"
    )

    todays_ipls_ids = get_todays_ipl().values_list("id", flat=True)

    if not lab_tests.exists():
        email.record_problem(
            "no lab tests added today",
            "Unable to find any lab tests added today"
        )

    batch_loaded_lab_tests = lab_tests.exclude(
        patient__initialpatientload__id__in=todays_ipls_ids
    )

    if not batch_loaded_lab_tests.exists():
        email.record_problem(
            "No lab tests loaded in batch patient loads",
            "Unable to find any lab tests loaded by batch loads today"
        )

    inital_loaded_lab_tests = lab_tests.filter(
        patient__initialpatientload__id__in=todays_ipls_ids
    )

    if not inital_loaded_lab_tests.exists():
        email.record_problem(
            "No lab tests loaded in inital patient loads",
            "Unable to find any lab tests added by initial patient loads today"
        )

    return email


def check_loads():
    email = ChecksEmailMessage()
    patients_should_have_been_added(email)
    amount_of_lab_tests_that_should_have_loaded(email)

    load_checks = [
        LoadCheck(
            email,
            "Initial Patient Load",
            models.InitialPatientLoad.objects.all(),
            min_daily_expected_amount=1,
            max_load_time=datetime.timedelta(seconds=600)
        ),
        LoadCheck(
            email,
            lab_test_service.SERVICE_NAME,
            models.BatchPatientLoad.objects.all(
                service_name=lab_test_service.SERVICE_NAME
            ),
            max_load_time=datetime.timedelta(seconds=600)
        ),
        LoadCheck(
            email,
            demographics_service.SERVICE_NAME,
            models.BatchPatientLoad.objects.all(
                service_name=demographics_service.SERVICE_NAME,
            ),
            max_load_time=datetime.timedelta(seconds=1200)
        )
    ]

    for load_check in load_checks:
        email = load_check.check()

    email.send_if_necessary()






