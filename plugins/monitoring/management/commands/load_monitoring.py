"""
One off initial data pull from google
"""
import csv
import datetime

from django.core.management.base import BaseCommand

from plugins.monitoring.models import Fact


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file')

    def flush(self):
        Fact.objects.all().delete()


    def handle(self, *args, **kwargs):
        self.flush()

        with open(kwargs['file'], 'r') as fh:
            reader = csv.reader(fh)
            headers = next(reader)
            for row in reader:
                date = datetime.datetime.strptime(row[0], '%d/%m/%Y %H:%M:%S')

                Fact(
                    when=date,
                    label='Total Patients',
                    value_int=int(row[1].replace(',', ''))
                ).save()

                Fact(
                    when=date,
                    label='Total Observations',
                    value_int=int(row[2].replace(',', ''))
                ).save()

                Fact(
                    when=date,
                    label='New Observations Per Load',
                    value_int=int(row[3].replace(',', ''))
                ).save()

                Fact(
                    when=date,
                    label='48hr Sync Minutes',
                    value_int=int(row[8].replace(',', ''))
                ).save()

                Fact(
                    when=date,
                    label='48hr Observations',
                    value_int=int(row[6].replace(',', ''))
                ).save()
