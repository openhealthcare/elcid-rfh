"""
A management command that does 2 things.

1. For an lab tests over 3 months ago. If all the observations
are pending, then delete the lab test.

2. Lab tests are updated if there is a new one

"""
from django.core.management.base import BaseCommand

class Command(BaseCommand):