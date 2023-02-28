from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

test_users = [
    "ohc", "emmanuel.wey"
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        User.objects.exclude(username__in=test_users).update(
            is_active=False
        )
