import datetime
import six
from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from intrahospital_api import deployment_check
from lab import models as lmodels


class Command(BaseCommand):

    def handle(self, *args, **options):
        since = timezone.now() - datetime.timedelta(
            seconds=60*60*4
        )
        result = {}
        try:
            deployment_check.check_since(since, result)
        except deployment_check.RollBackError:
            six._print(result)
        except Exception as e:
            pass

