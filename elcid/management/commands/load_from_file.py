import json, os
from elcid import gloss_api

from django.contrib.auth.models import User

from django.core.management.base import BaseCommand

from opal.models import Patient

from lab.models import LabTest


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', help="the file name to load from"
            )
        parser.add_argument(
            'patient', help="attribute all subrecords to a ", type=int
        )

    def handle(self, *args, **options):
        data = json.loads(open(options['filename'], 'r').read())
        patient = Patient.objects.get(id=options['patient'])
        data["hospital_number"] = patient.demographics_set.get().hospital_number

        patient.labtest_set.all().delete()
        gloss_api.bulk_create_from_gloss_response(data)
        print 'Added to', patient
