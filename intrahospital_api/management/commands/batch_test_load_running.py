"""
    returns the current status of the lab test load
"""

import json
from django.core.management.base import BaseCommand
from intrahospital_api import loader


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(
            json.dumps(
                dict(status=loader.any_loads_running()), indent=4
            )
        )
