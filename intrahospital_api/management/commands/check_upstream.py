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


class DisplayField:
    """
    A class that sorts out whether a field is in error or
    not and provides flags for the template.

    A warning is flagged for 2 reasons.
        1. A table is throwing an error when we try and query it
        2. A table was updated within the last 48 hours but not
           in the last 24 hours.

    An old warning is flagged if a table has not been updated in the
    last 48 hours.
    """
    def __init__(self, counts, last_updated):
        self.counts = counts
        self.last_updated = last_updated
        self.warning = False
        self.old_warning = False
        self.colour = "black"
        two_days_ago = timezone.now() - datetime.timedelta(2)

        if isinstance(counts, str):
            self.warning = True

        if counts == 0:
            if self.last_updated > two_days_ago:
                self.warning = True
                self.colour = "red"
            else:
                self.old_warning = True
                self.colour = "brown"


class Command(BaseCommand):
    help = "Check that the upstream results are up and populated"
    template_name = "emails/check_upstream.html"

    def send_email(self, ctx):
        warning = False
        old_warning = False
        if any([i.warning for i in ctx.values()]):
            warning = True
        elif any([i.old_warning for i in ctx.values()]):
            old_warning = True

        title = f"{settings.OPAL_BRAND_NAME} view counts"

        if warning:
            title = f"{title} WARNING"
        elif old_warning:
            title = f"{title} OLD WARNING"
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

    def updated_recently(self, view, field, trust=False):
        query = f"SELECT MAX({field}) FROM {view}"
        try:
            if trust:
                last_updated = self.api.execute_trust_query(query)
            else:
                last_updated = self.api.execute_hospital_query(query)
            return last_updated[0]
        except Exception as e:
            return str(e)

    def count_last_24_hours(self, view, field, trust=False):
        query = f"SELECT COUNT(*) FROM {view} WHERE {field} > @since"
        params = {"since": self.yesterday}
        try:
            if trust:
                cnt = self.api.execute_trust_query(query, params)

            else:
                cnt = self.api.execute_hospital_query(query, params)
            return cnt[0]
        except Exception as e:
            return str(e)

    def get_context_data(self):
        display_fields = {}

        for view, field in HOSPITAL_TABLES.items():
            display_fields[view] = DisplayField(
                self.count_last_24_hours(view, field, trust=False),
                self.updated_recently(view, field, trust=False)
            )
        for view, field in TRUST_TABLES.items():
            display_fields[view] = DisplayField(
                self.count_last_24_hours(view, field, trust=True),
                self.updated_recently(view, field, trust=True)
            )

        return display_fields

    def handle(self, *args, **kwargs):
        try:
            self.api = get_api()
            self.yesterday = timezone.now() - datetime.timedelta(1)
            ctx = self.get_context_data()
            self.send_email(ctx)
        except Exception as e:
            logger.error(f'Failed to check upstream with "{e}"')



