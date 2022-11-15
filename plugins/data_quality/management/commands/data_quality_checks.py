from django.core.management.base import BaseCommand
from plugins.data_quality.checks import daily, monthly


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--daily',
            action='store_true'
        )
        parser.add_argument(
            '--monthly',
            action='store_true'
        )


    def handle(self, *args, **options):
        if options["daily"]:
            for check in daily:
                check()
        if options["monthly"]:
            for check in monthly:
                check()
