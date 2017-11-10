from django.db import transaction
from django.core.management.base import BaseCommand
from elcid.models import Demographics
from intrahospital_api.models import ExternalDemographics


class Command(BaseCommand):
    def update_demographics(self, external_demographics):
        demographics = Demographics.objects.filter(
            first_name__iexact=external_demographics.first_name,
            surname__iexact=external_demographics.surname,
            date_of_birth=external_demographics.date_of_birth,
            hospital_number=external_demographics.hospital_number
        )

        # we can't do an update because of fk ft
        for demographic in demographics:
            demographic.external_system = "RFH Database"
            demographic.sex = external_demographics.sex
            demographic.title = external_demographics.title
            demographic.save()

    @transaction.atomic
    def handle(self, *args, **options):
        for e in ExternalDemographics.objects.all():
            self.update_demographics(e)
