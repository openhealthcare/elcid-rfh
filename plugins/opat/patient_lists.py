from elcid.patient_lists import RfhPatientList
from opal.core.patient_lists import TaggedPatientList



class OPATCurrent(RfhPatientList, TaggedPatientList):
    display_name = 'OPAT current'
    direct_add = True
    tag = 'opat_current'
    template_name = 'episode_list.html'
    schema = []


class OPATMonitoring(RfhPatientList, TaggedPatientList):
    display_name = 'OPAT monitoring'
    direct_add = True
    tag = 'opat_monitoring'
    template_name = 'episode_list.html'
    schema = []