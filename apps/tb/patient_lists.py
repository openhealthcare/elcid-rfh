"""
Patient lists for the TB module
"""
import datetime

from opal.core import patient_lists
from opal.models import Episode

class TBPatientConsultationsToday(patient_lists.PatientList):
    display_name  = "TB Consults Today"
    slug          = "tb-consults-today"
    template_name = 'patient_lists/collapsed_list.html'
    schema        = []

    def get_queryset(self, user=None):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        episodes  = Episode.objects.filter(patientconsultation__when__gte=yesterday)
        return episodes
