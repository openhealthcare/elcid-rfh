"""
Management command to periodically re-calculate the
Covid 19 Dashboard stats.
"""
from django.core.management.base import BaseCommand

from plugins.covid import calculator


class Command(BaseCommand):

    def handle(self, *args, **options):

        calculator.calculate()
