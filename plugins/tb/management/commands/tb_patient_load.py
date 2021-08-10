"""
Management command to create patients/episodes for the tb service.
"""
from django.core.management.base import BaseCommand
from plugins.tb import loader


class Command(BaseCommand):
    def handle(self, *args, **options):
        loader.create_patients_from_tb_tests()
        loader.create_tb_episodes_for_appointments()
