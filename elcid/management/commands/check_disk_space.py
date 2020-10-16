"""
Management command to check disk space on a server.
"""
import datetime
import subprocess

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from plugins.monitoring.models import Fact


def raise_the_alarm():
    msg = "Routine system check on {} has detected a volume with > 90% disk usage. Please log in and investigate."
    send_mail(
        "{} Disk Space Alert: Action Required".format(settings.OPAL_BRAND_NAME),
        msg.format(settings.OPAL_BRAND_NAME),
        settings.DEFAULT_FROM_EMAIL,
        [i[1] for i in settings.ADMINS]
    )


class Command(BaseCommand):
    def handle(self, *a, **k):
        p1 = subprocess.Popen(["df", "-h"], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["awk", "{print $5}"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p3 = subprocess.Popen(["egrep", "9[0-9]%"], stdin=p2.stdout, stdout=subprocess.PIPE)
        out, er = p3.communicate()
        if out:
            raise_the_alarm()

        p1 = subprocess.Popen(["df", "-h"], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "sda2"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["awk", "{print $5}"], stdin=p2.stdout, stdout=subprocess.PIPE)
        out, err = p3.communicate()
        disk_usage = int(out[:2])

        Fact(
            when=datetime.datetime.now(),
            label="Disk Usage Percentage",
            value_int=disk_usage
        ).save()

        return
