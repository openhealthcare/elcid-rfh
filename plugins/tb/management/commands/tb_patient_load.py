"""
Management command to create patients/episodes for patients
who have a TB appointment if they do not already exist.
"""
from django.core.management.base import BaseCommand
from plugins.tb import loader


class Command(BaseCommand):
    def handle(self, *args, **options):
        loader.create_tb_episodes()
