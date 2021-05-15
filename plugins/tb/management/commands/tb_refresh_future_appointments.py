from django.core.management.base import BaseCommand
from plugins.tb import loader


class Command(BaseCommand):
    def handle(self, *args, **options):
        loader.refresh_future_tb_appointments()
