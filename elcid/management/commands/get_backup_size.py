"""
Management command to track the size of our backups.
Run by cron
"""
import datetime
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from plugins.monitoring.models import Fact


class Command(BaseCommand):
    def handle(self, *a, **k):
        fmt = '/usr/lib/ohc/var/back.{}.elcidrfh_v{}.sql'
        size_bytes = os.path.getsize(
            fmt.format(
                datetime.date.today().strftime('%d.%m.%Y'),
                settings.VERSION_NUMBER.replace('.', ''))
        )

        mb = size_bytes/1073741824
        mb = "{:.2f}".format(mb)
        Fact(
            when=timezone.make_aware(datetime.datetime.now()),
            label="Backup size (MB)",
            value_float=mb
        ).save()
