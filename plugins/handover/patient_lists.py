"""
Patient lists for the handover plugin
"""
from opal.core.patient_lists import PatientList
from opal.models import Episode

from elcid.patient_lists import RfhPatientList


class AMTList(RfhPatientList, PatientList):
    is_read_only  = True
    schema        = []
    template_name = 'episode_list.html'
    display_name  = 'Auto AMT'
    order         = 50

    @property
    def queryset(self):
#        patients = Patient.objects.filter()
        return Episode.objects.filter(patient__amt_handover__discharged='N')

    @classmethod
    def visible_to(klass, user):
        return user.is_superuser
