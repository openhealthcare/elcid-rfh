"""
Management command to periodically re-calculate the
AMT Covid 19 Dashboard stats.
"""
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from plugins.covid.models import CovidAcuteMedicalDashboardReportingDay
from plugins.handover.models import AMTHandover

class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):

        CovidAcuteMedicalDashboardReportingDay.objects.all().delete()

        target = timezone.make_aware(datetime.datetime(2020, 3, 1))

        today = datetime.date.today()
        today = timezone.make_aware(
            datetime.datetime(year=today.year, month=today.month, day=today.day))

        while target < today:
            next_day = target + datetime.timedelta(days=1)

            take = AMTHandover.objects.filter(
                referral_added__gt=target,
                referral_added__lt=next_day
            )

            covid = take.filter(rota='COVID')
            non_covid = take.filter(rota='NON-COVID')
            print(target)
            print(take.count())
            CovidAcuteMedicalDashboardReportingDay(
                date=target, patients_referred=take.count(),
                covid=covid.count(), non_covid=non_covid.count()
            ).save()

            target = next_day
