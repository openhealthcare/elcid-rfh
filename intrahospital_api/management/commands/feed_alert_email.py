"""
A management command run by a daily cron job that
sends an email if one of the feeds has not loaded
that day.
"""
import datetime
import traceback
from django.db.models import Max
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from plugins.appointments.models import Appointment
from plugins.labtests.models import Observation
from plugins.imaging.models import Imaging
from elcid.models import MasterFileMeta
from intrahospital_api import logger


def send_email(title, context):
    template_name = "email/feed_alert.html"
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    send_mail(
        title,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMINS,
        html_message=html_message,
    )


def check_feeds():
    """
    Note we can't use the created timestamps in our system
    because new patients will load in upstream data and although
    that data will be old, the upstream timestamps in our
    system will be new.
    """
    errors = []
    str_format = '%d/%m/%Y %H:%M:%S'
    today = datetime.date.today()
    email_ctx = {'today': today}

    # Check Lab tests
    observation_last_updated = Observation.objects.aggregate(
        max_updated=Max('last_updated')
    )["max_updated"]
    if not observation_last_updated.date() == today:
        observation_last_updated_str = observation_last_updated.strftime(str_format)
        errors.append(f"No Lab tests loaded since {observation_last_updated_str}")
    email_ctx["Last observation updated"] = observation_last_updated

    # Check Appointments
    appointment_dts = Appointment.objects.aggregate(
        max_updated=Max('last_updated'),
        max_inserted=Max('insert_date')
    )
    last_appointment = max([
        appointment_dts["max_updated"],
        appointment_dts["max_inserted"]
    ])
    if not last_appointment.date() == today:
        last_appointment_str = last_appointment.strftime(str_format)
        errors.append(f"No Appointments loaded since {last_appointment_str}")
    email_ctx["Last appointment updated/inserted"] = last_appointment

    # Check Imaging
    imaging_last_reported = Imaging.objects.aggregate(
        max_date_reported=Max('date_reported')
    )["max_date_reported"]
    if not imaging_last_reported.date() == today:
        imaging_last_reported_str = imaging_last_reported.strftime(str_format)
        errors.append(f"No Imaging loaded since {imaging_last_reported_str}")
    email_ctx["Last imaging date reported"] = imaging_last_reported

    # Check Patient information
    crs_master_file_last_updated = MasterFileMeta.objects.aggregate(
        max_updated=Max("last_updated")
    )["max_updated"]
    if not crs_master_file_last_updated.date() == today:
        crs_last_updated_str = crs_master_file_last_updated.strftime(
            str_format
        )
        errors.append(f"No patient information loaded since {crs_last_updated_str}")
    email_ctx["Last crs masterfile updated"] = crs_master_file_last_updated
    if len(errors):
        title = f"ALERT {settings.OPAL_BRAND_NAME}:" + ", ".join(errors)
        send_email(title, email_ctx)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            check_feeds()
        except Exception:
            msg = f'Exception running the feed_alert_email \n {traceback.format_exc()}'
            logger.error(msg)
