"""
We read from quite a few tables which we don't control

Lets acrue some numbers for inserted in the previous day

If there are none or an error, add WARNING to the email
"""
import datetime
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import send_mail
from intrahospital_api import get_api
from intrahospital_api import logger

HOSPITAL_TABLES = {
    "VIEW_ElCid_CRS_OUTPATIENTS": "insert_date",
    "VIEW_ElCid_ITU_Handover": "sqlserver_lastupdated_datetime",
    "VIEW_ElCid_Radiology_Results": "date_reported",
    "CRS_ENCOUNTERS": "insert_date",
    "VIEW_ElCid_CRS_OUTPATIENTS": "insert_date",
    "VIEW_ElCid_Freenet_TTA_Main": "last_updated",
    "VIEW_ElCid_Freenet_TTA_Drugs": "last_updated",
    "VIEW_CRS_Patient_Masterfile": "LAST_UPDATED"
}


TRUST_TABLES = {
    "tQuest.Pathology_Result_view": "date_inserted"
}


class WarningField:
    """
    A class to flag that a field should be marked
    as needing a warning in the template
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __eq__(self, k):
        if not isinstance(k, WarningField):
            return False
        return self.value == k.value

    @property
    def warning(self):
        if isinstance(self.value, str) or self.value == 0:
            return True
        return False


class Command(BaseCommand):
    help = "Check that the upstream results are up and populated"
    template_name = "emails/check_upstream.html"

    def send_email(self, ctx):
        warning = False
        if any([i.warning for i in ctx.values()]):
            warning = True

        title = f"{settings.OPAL_BRAND_NAME} view counts"

        if warning:
            title = f"{title} WARNING"
        html_message = render_to_string(
            self.template_name, {
                "context": ctx,
                "title": title
            }
        )
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

    def get_context_data(self):
        api = get_api()
        counts = {k: 0 for k in HOSPITAL_TABLES.keys()}

        for k in TRUST_TABLES.keys():
            counts[k] = 0

        last_24_hours = timezone.now() - datetime.timedelta(1)

        for view, field in HOSPITAL_TABLES.items():
            query = f"SELECT COUNT(*) FROM {view} WHERE {field} > @since"
            try:
                cnt = api.execute_hospital_query(
                    query, params={"since": last_24_hours}
                )
                counts[view] = cnt[0]
            except Exception as e:
                counts[view] = str(e)

        for view, field in TRUST_TABLES.items():
            query = f"SELECT COUNT(*) FROM {view} WHERE {field} > @since"
            try:
                cnt = api.execute_trust_query(
                    query, params={"since": last_24_hours}
                )
                counts[view] = cnt[0]
            except Exception as e:
                counts[view] = str(e)
        return {k: WarningField(i) for k, i in counts.items()}

    def handle(self, *args, **kwargs):
        try:
            ctx = self.get_context_data()
            self.send_email(ctx)
        except Exception as e:
            logger.error('Failed to check upstream with "{e}"')



