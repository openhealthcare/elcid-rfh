"""
Management command to look and see if patients have follow up
appointments upstream and if so to create those patients
"""
from django.core.management.base import BaseCommand

from plugins.covid import loader


class Command(BaseCommand):

    def handle(self, *args, **options):
        loader.create_followup_episodes()
