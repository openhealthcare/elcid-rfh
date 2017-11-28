# so the theory is, we load in data, if they're the same, we're fine
# if they are different on first name last name hospital number, nhs number date of birth
# we blow up
# if they are the same what we would really like to do is mark them as resolved?

# curent plan, load in all demographics for patients
# store them in a seperate table
# we have a resolved tab and a to resolved


# other options, we automatically resolve all patients that match on 2 fields
# we update them accordingly and add in the external system, that's how we know they
# are resolved

# then we have partial demographics matches that we load in
# then we have missing demographics

# in terms of the code we look up via hosptial number,
# then by surname and date of birth as they have an index on hospital number

# we bring them all in and then display them as matches in its own page
# we then need to build the form part of it.
import datetime
from django.db import transaction
from intrahospital_api import get_api
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from opal.models import Patient


class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):
        api = get_api()
        user = User.objects.get(username="ohc")
        patients = Patient.objects.filter(demographics__external_system=None)
        for patient in patients:
            demographics = patient.demographics_set.get()
            external_demographics_json = api.demographics(
                demographics.hospital_number
            )
            if not external_demographics_json:
                print "unable to find {}".format(demographics.hospital_number)
                continue

            external_demographics = patient.externaldemographics_set.get()
            external_demographics_json.pop('external_system')

            if external_demographics_json["date_of_birth"]:
                db = datetime.datetime.combine(
                    external_demographics_json["date_of_birth"],
                    datetime.datetime.min.time()
                ).strftime(settings.DATE_INPUT_FORMATS[0])

                external_demographics_json["date_of_birth"] = db
            external_demographics.update_from_dict(
                external_demographics_json, user
            )
