import json, os

from django.contrib.auth.models import User

from django.core.management.base import BaseCommand

from opal.models import Patient

from lab.models import LabTest

class Command(BaseCommand):
    def handle(self, *args, **options):
        data = json.loads(open(os.path.expanduser("~/Downloads/test_info.json"), 'r').read())
        tests = [t for t in data['lab_test'] if t['lab_test_type'] == 'HL7Result']
        patient = Patient.objects.first()

        patient.labtest_set.all().delete()

        user = User.objects.first()

        for t in tests:
            t['lab_test_type'] = "HL7 Result"
            del t['created_by_id']
            del t['id']
            t['patient_id'] = patient.id

            LabTest().update_from_dict(t, user)
            print t['external_identifier']

        print 'Added to', patient
