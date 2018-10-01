"""
A management command that looks at the last x hours
(by default 4) and makes sure the batch load
and the inital load all load are all the same.

This should only run on test and will blow up if you
try and run it outside of test
"""

import datetime
import six
from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from intrahospital_api import deployment_check


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'hours',
            help="hours ago",
            type=int,
            default=4
        )

    def handle(self, *args, **options):
        result = {}

        since = timezone.now()- datetime.timedelta(
            seconds=options["hours"] * 60 * 60
        )

        try:
            deployment_check.check_since(since, result)
        except deployment_check.RollBackError:
            six._print(result)
        except Exception as e:
            pass

