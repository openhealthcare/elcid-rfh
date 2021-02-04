"""
Management command to fetch all encounters for our patients
"""
import datetime
import time
import traceback

from django.core.management import BaseCommand
from django.utils import timezone
from opal.models import Patient

from plugins.monitoring.models import Fact

from plugins.admissions import loader, logger, models

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        try:
            t1 = time.time()
            loader.load_recent_encounters()
            t2 = time.time()

            when             = timezone.make_aware(datetime.datetime.fromtimestamp(t1))
            minutes_taken    = int(int(t2-t1)/60)
            total_encounters = models.Encounter.objects.all().count()

            Fact(when=when, label='Encounter Load Minutes', value=minutes_taken).save()
            Fact(when=when, label='Total Encounters', value=total_encounters).save()

        except Exception:
            msg += "Loading encounters:  \n{}".format(traceback.format_exc())
            logger.error(msg)
        return
