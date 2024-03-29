"""
Management command
"""
import datetime
from django.db import transaction

from django.core.management.base import BaseCommand

from plugins.admissions import models


def strip_wardname(wardname):
    """
    The same ward can come through with at least two
    different prefixes. Stripping these allows us
    to treat them as the same place
    """
    if wardname is None:
        return None
    if wardname.startswith('RAL '):
        return wardname.replace('RAL ', '')
    if wardname.startswith('RF-'):
        return wardname.replace('RF-', '')
    return wardname


def strip_bedname(bedname):
    """
    The reporting of beds from upstream varies over time
    we uppercase and remove spaces to avoid duplication

    Occasionally ben names come in just as e.g. 14
    """
    if bedname is None:
        return None
    name = bedname.upper().replace(' ', '')

    if len(name) == 2:
        name = f"BED{name}"

    if name.endswith('BED'):
        name = "BED" + name[:2]

    if name.endswith('COT'):
        name = "COT" + name[:2]

    return name


class Command(BaseCommand):
    @transaction.atomic
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

        beds = {}

        for encounter in encounters:
            key = (
                encounter.pv1_3_building,
                strip_wardname(encounter.pv1_3_ward),
                strip_bedname(encounter.pv1_3_bed)
            )

            beds[key] = encounter

        locations = [
            models.UpstreamLocation(
                building=e.pv1_3_building,
                ward=strip_wardname(e.pv1_3_ward),
                room=e.pv1_3_room,
                bed=strip_bedname(e.pv1_3_bed),
                hospital=e.pv1_3_hospital,
                patient=e.patient,
                admitted=e.pv1_44_admit_date_time,
                encounter=e
            )
            for e in beds.values()
        ]

        models.UpstreamLocation.objects.bulk_create(locations)
