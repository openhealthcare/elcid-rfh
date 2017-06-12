import json, os

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
        tests = [t for t in data['lab_test'] if t['lab_test_type'] == 'HL7Result']
        patient = Patient.objects.get(id=options['patient'])

        if not patient:
            patient = Patient.objects.create()

        patient.labtest_set.all().delete()

        user = User.objects.first()

        for t in tests:
            t['lab_test_type'] = "HL7 Result"
            del t['created_by_id']
            del t['id']
            t['patient_id'] = patient.id
            LabTest().update_from_dict(t, user)
            print t['external_identifier']
            import pprint;
            pprint.pprint(t)

        print 'Added to', patient
