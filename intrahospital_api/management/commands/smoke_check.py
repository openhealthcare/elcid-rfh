import datetime
from django.core.management.base import BaseCommand
from intrahospital_api import models
from intrahospital_api import smoke_check


class Command(BaseCommand):
    """
    A command that checks that all loads
    are performing according to expectations
    """
    def handle(self, *args, **kwargs):
        smoke_check.check_loads()
