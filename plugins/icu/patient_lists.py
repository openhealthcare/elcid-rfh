"""
Patient lists for our ICU plugin
"""
from opal.core.patient_lists import PatientList
from opal.models import Episode

from elcid.patient_lists import RfhPatientList



class AutoICUSouthList(RfhPatientList, PatientList):
    is_read_only  = True
    schema        = []
    template_name = 'episode_list.html'
    display_name  = 'Auto ICU South'
    order         = 30

    @property
    def queryset(self):
        return Episode.objects.filter(
            patient__icuhandoverlocation__ward='South'
        )

    @classmethod
    def visible_to(klass, user):
        return user.is_superuser
