"""
Management command that checks that lab tests have been synced for the auto
add ITU lists and bacteraemia.

It resyncs those patients and sends an email with the result
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from plugins.icu.patient_lists import AutoICUSouthList, AutoICUEastList, AutoICUWestList
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from plugins.labtests.models import Observation
from opal.models import Patient
from elcid.patient_lists import Bacteraemia
from elcid.utils import timing
from intrahospital_api import loader
from plugins.labtests import logger


def get_patients():
    """
    Returns a list of patients to have their lab tests checked
    """
    patient_ids = set()
    patient_lists = [AutoICUSouthList, AutoICUEastList, AutoICUWestList, Bacteraemia]
    for patient_list in patient_lists:
        qs = patient_list().get_queryset()
        qs = qs.select_related('patient')
        for episode in qs:
            patient_ids.add(episode.patient_id)
    return Patient.objects.filter(id__in=patient_ids)


def get_observations_count(patients):
    return Observation.objects.filter(test__patient__in=patients).count()


def sync_patients(patients):
    for patient in patients:
        loader.sync_patient(patient)


def create_email(patients, before_observation_count, after_observation_count):
    template_name = "email/table_email.html"
    title = f"{settings.OPAL_BRAND_NAME} ICU & Bacteraemia lab test counts"
    if not before_observation_count == after_observation_count:
        title = f"{title} WARNING"

    table_context = {
        "Patient count": len(patients),
        "Before patient sync count": before_observation_count,
        "After patient sync count": after_observation_count,
    }

    send_email(title, template_name, {"table_context": table_context, "title": title})


def send_email(title, template_name, context):
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    admin_emails = ", ".join([i[1] for i in settings.ADMINS])
    logger.info(f"sending email {title} to {admin_emails}")
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
        patients = get_patients()
        before_observation_count = get_observations_count(patients)
        sync_patients(patients)
        after_observation_count = get_observations_count(patients)
        create_email(patients, before_observation_count, after_observation_count)
