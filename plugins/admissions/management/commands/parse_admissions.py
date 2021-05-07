"""
Management command
"""
import datetime

from django.core.management.base import BaseCommand

from plugins.admissions import models


class Command(BaseCommand):

    def handle(self, *a, **k):

        models.UpstreamLocation.objects.all().delete()

        today = datetime.date.today()
        start = today - datetime.timedelta(days=9*30)

        encounters = models.Encounter.objects.filter(
            pv1_45_discharge_date_time__isnull=True,
            pv1_44_admit_date_time__gte=start,
        ).exclude(
            pv1_3_bed__isnull=True
        ).exclude(
            msh_9_msg_type='A23'
        ).exclude(
            evn_2_movement_date__isnull=True
        ).order_by('evn_2_movement_date')

        for encounter in encounters:
            location, _ = models.UpstreamLocation.objects.get_or_create(
                building=encounter.pv1_3_building,
                ward=encounter.pv1_3_ward,
                room=encounter.pv1_3_room,
                bed=encounter.pv1_3_bed
            )
            location.hospital  = encounter.pv1_3_hospital
            location.patient   = encounter.patient
            location.admitted  = encounter.pv1_44_admit_date_time
            location.encounter = encounter

            location.save()
            self.stdout.write('.')
