"""
A management command that is run by a cron job
"""
import datetime
import time
from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils import timezone
from opal.models import Patient

from elcid.models import Demographics
from elcid import utils
from intrahospital_api.loader import api
from intrahospital_api import update_lab_tests
from plugins.labtests.models import Observation
from plugins.labtests import logger
from plugins.monitoring.models import Fact

MAX_AMOUNT = 300000


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
    utils.send_email("Too many labtests", msg)


class Command(BaseCommand):

    def handle(self, *args, **options):
        pre_obs = Observation.objects.all().count()
        kw = {
            'patients': Patient.objects.all().count(),
        }

        t1 = time.time()
        obs_count = 0

        since = datetime.datetime.now() - datetime.timedelta(hours=48)

        tquery1 = time.time()

        # Loading too many rows at once causes memory issues.
        # The max amount is significantly more than we expect
        # so if we receive more, email admins and return.
        count = get_count(since)
        if count > MAX_AMOUNT:
            send_too_many_email(since, count)
            return
        data = api.data_deltas(since)
        tquery2 = time.time()

        demographics_set = Demographics.objects.all()

        for item in data:
            obs_count += len(item['lab_tests'])

            patient_demographics_set = demographics_set.filter(
                hospital_number=item['demographics']["hospital_number"]
            )

            if not item['demographics']["hospital_number"]:
                continue

            if not patient_demographics_set.exists():
                continue  # Not in our cohort

            update_patient(patient_demographics_set.first().patient,  item["lab_tests"])

        t2 = time.time()

        kw['total_obs'] = Observation.objects.all().count()
        kw['obs_diff'] = kw['total_obs'] - pre_obs
        kw['time'] = int(t2-t1)
        kw['upstream_query_time'] = int(tquery2 - tquery1)
        kw['48hr_obs'] = obs_count

        # Save as Facts
        when = timezone.make_aware(datetime.datetime.fromtimestamp(t1))
        Fact(
            when=when,
            label='Total Patients',
            value_int=kw['patients']
        ).save()

        Fact(
            when=when,
            label='Total Observations',
            value_int=kw['total_obs']
        ).save()

        Fact(
            when=when,
            label='New Observations Per Load',
            value_int=kw['obs_diff']
        ).save()

        Fact(
            when=when,
            label='48hr Sync Minutes',
            value_int=int(kw['time']/60)
        ).save()

        Fact(
            when=when,
            label='48hr Observations',
            value_int=kw['48hr_obs']
        ).save()
