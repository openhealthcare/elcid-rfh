"""
Patient lists for the TB module
"""
import datetime

from django.utils import timezone
from opal.core import patient_lists
from opal.models import Episode

class TBPatientConsultationsToday(patient_lists.PatientList):
    display_name  = "TB Consults Today"
    slug          = "tb-consults-today"
    template_name = 'patient_lists/collapsed_list.html'
    schema        = []
    order         = 60

    def get_queryset(self, user=None):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        episodes  = Episode.objects.filter(
            patientconsultation__when__gte=yesterday)
        return episodes
