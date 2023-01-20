"""
Batch load 3 is 2-3x faster than batch load 2 because
it speeds batches things together
"""
import datetime
import time
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from opal.models import Patient

from elcid.models import Demographics
from intrahospital_api.loader import api
from intrahospital_api import update_lab_tests
from plugins.labtests.models import Observation
from plugins.labtests import logger
from plugins.monitoring.models import Fact

MAX_AMOUNT = 250000


@transaction.atomic
def update_patient(patient, lab_tests):
    update_lab_tests.update_tests(patient, lab_tests)


def get_count(since):

    query = """
    SELECT count(*)
    FROM tQuest.Pathology_Result_View
    WHERE date_inserted >= @since
    """
    return api.execute_trust_query(query, params={"since": since})[0][0]


def send_too_many_email(since_dt, count):
    str_format = '%d/%m/%Y %H:%M:%S'
    since = since_dt.strftime(str_format)
    msg = "\n".join([
        f"Trying to lab tests load since {since}.",
        f"We found {count} lab tests which is over the threshold of {MAX_AMOUNT}.",
        "Cancelling the load"
    ])
    logger.info(f"batch_load2: {msg}")
    send_mail(
        f"{settings.OPAL_BRAND_NAME}: Too many labtests",
        msg,
        settings.DEFAULT_FROM_EMAIL,
        [i[1] for i in settings.ADMINS]
    )


class Command(BaseCommand):

    def handle(self, *args, **options):
        pre_obs = Observation.objects.all().count()
        t1 = time.time()

        since = datetime.datetime.now() - datetime.timedelta(hours=48)

        tquery1 = time.time()
        data = api.data_deltas(since)
        tquery2 = time.time()
        update_lab_tests.update_lab_tests_from_query(data)
        t2 = time.time()
        obs_count = Observation.objects.all().count()
        print(f"Total Observations {obs_count}")
        print(f"Obs diff {obs_count - pre_obs}")
        print(f"Update time {int(t2-t1)}")
        print(f"Upstream query time {int(tquery2 - tquery1)}")
