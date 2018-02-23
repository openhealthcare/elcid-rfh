from django.core.management.base import BaseCommand
from intrahospital_api.loader import update_external_demographics


class Command(BaseCommand):
    def handle(self, *args, **options):
        update_external_demographics()
