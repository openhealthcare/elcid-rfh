from opal.models import Episode
from opal.core import patient_lists


class TbPatientList(patient_lists.PatientList):
    display_name = 'TB Service Patients'

    queryset = Episode.objects.all

    schema = [
        patient_lists.Column(title='TB', template_path='apps/tb/templates/records/tb.html')
    ]
