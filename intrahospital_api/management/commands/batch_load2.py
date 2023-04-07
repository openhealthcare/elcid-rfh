"""
A management command that is run by a cron job
"""
import datetime
import time
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from opal.models import Patient

from elcid import utils
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

        mrns = [item['demographics']["hospital_number"] for item in data]
        patient_to_mrn = utils.find_patients_from_mrns(mrns)

        for item in data:
            obs_count += len(item['lab_tests'])
            mrn = item['demographics']["hospital_number"]
            patient = patient_to_mrn.get(mrn)
            # The patient is not in our cohort
            if not patient:
                continue
            update_patient(patient,  item["lab_tests"])

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
