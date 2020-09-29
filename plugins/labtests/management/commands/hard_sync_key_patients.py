"""
Management command that forces a hard sync of lab tests for key patients.
"""
import datetime
import time
from collections import OrderedDict

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from opal.models import Patient, PatientRecordAccess

from elcid.patient_lists import Bacteraemia
from elcid.utils import timing
from intrahospital_api import loader, update_lab_tests
from plugins.icu.patient_lists import AutoICUSouthList, AutoICUEastList, AutoICUWestList
from plugins.labtests.models import Observation
from plugins.labtests import logger


def get_patients():
    """
    Returns a list of patients to have their lab tests checked
    """
    patient_ids = set()
    patient_lists = [AutoICUSouthList, AutoICUEastList, AutoICUWestList, AutoICU2List, Bacteraemia]

    for patient_list in patient_lists:
        qs = patient_list().get_queryset()
        qs = qs.select_related('patient')
        for episode in qs:
            patient_ids.add(episode.patient_id)

    recent = PatientRecordAccess.objects.filter(
        created__gte=datetime.datetime.now()-datetime.timedelta(days=21))
    for access in recent:
        patient_ids.add(access.patient_id)

    return Patient.objects.filter(id__in=patient_ids)


def get_observations_count(patients):
    return Observation.objects.filter(test__patient__in=patients).count()


def sync_patients(patients):
    for patient in patients:
        results = loader.api.results_for_hospital_number(
            patient.demographics().hospital_number
        )
        update_lab_tests.upd_tests(patient, results)


def create_email(patients, before_observation_count, after_observation_count, time_taken):
    template_name = "email/table_email.html"
    title = "{} ICU & Bacteraemia lab test counts".format(
        settings.OPAL_BRAND_NAME
    )
    if not before_observation_count == after_observation_count:
        title = "{} WARNING".format(title)

    table_context = OrderedDict((
        ("Patient count", len(patients),),
        ("Before patient sync count", before_observation_count,),
        ("After patient sync count", after_observation_count,),
        ("Seconds", time_taken)
    ))

    send_email(title, template_name, {"table_context": table_context, "title": title})


def send_email(title, template_name, context):
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    admin_emails = ", ".join([i[1] for i in settings.ADMINS])
    logger.info("sending email {} to {}".format(
        title, admin_emails
    ))
    send_mail(
        title,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMINS,
        html_message=html_message,
    )


class Command(BaseCommand):
    @timing
    def handle(self, *a, **k):
        t1 = time.time()
        patients = get_patients()
        before_observation_count = get_observations_count(patients)
        sync_patients(patients)
        after_observation_count = get_observations_count(patients)
        t2 = time.time()

        create_email(patients, before_observation_count, after_observation_count, int(t2-t1))
