"""
A management command that is run by a cron job
"""
import datetime
import time
from django.db import transaction
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from opal.models import Patient

from elcid.models import Demographics
from intrahospital_api.loader import api
from intrahospital_api import update_lab_tests
from plugins.labtests.models import Observation
from plugins.monitoring.models import Fact

def send_email(title, template_name, context):
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    send_mail(
        title,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMINS,
        html_message=html_message,
    )

def create_email(**kwargs):
    template_name = "email/table_email.html"
    title = f"{settings.OPAL_BRAND_NAME} new results sync"
    send_email(title, template_name, {"table_context": kwargs, "title": title})


@transaction.atomic
def update_patient(patient, lab_tests):
    update_lab_tests.update_tests(patient, lab_tests)


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
                continue # Not in our cohort

            item['lab_tests'] = [i for i in item['lab_tests'] if i["test_name"] or i["external_identifier"]]
            update_patient(patient_demographics_set.first().patient,  item["lab_tests"])


        t2 = time.time()

        kw['total_obs'] = Observation.objects.all().count()
        kw['obs_diff'] = kw['total_obs'] - pre_obs
        kw['time'] = int(t2-t1)
        kw['upstream_query_time'] = int(tquery2 - tquery1)
        kw['48hr_obs'] = obs_count
        create_email(**kw)

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
