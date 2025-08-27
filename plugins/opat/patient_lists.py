"""
Patient list definitions for the OPAT plugin
"""
from opal import models as omodels
from opal.core.patient_lists import TaggedPatientList

from elcid.patient_lists import RfhPatientList
from elcid import models


from plugins.opat import models as opat_models
from plugins.tb import models as tb_models

class OPATPatientList(RfhPatientList):

    PATIENT_LIST_SUBRECORDS = [
        models.PrimaryDiagnosis,
        models.Demographics,
        models.Antimicrobial,
        models.Diagnosis,
        models.Location,
        models.ChronicAntifungal,
        omodels.Tagging,
        opat_models.OPATRecord,
        opat_models.RelevantOpatBackground,
        models.Imaging,
        tb_models.Allergies,
        tb_models.Treatment,
        models.MicrobiologyInput
    ]


class OPATCurrent(OPATPatientList, TaggedPatientList):
    display_name = 'OPAT Current'
    direct_add = True
    tag = 'opat_current'
#    template_name = 'episode_list.html'
    template_name = 'opat_episode_list.html'
    schema = []


class OPATMonitoring(OPATPatientList, TaggedPatientList):
    display_name = 'OPAT Monitoring'
    direct_add = True
    tag = 'opat_monitoring'
    template_name = 'opat_episode_list.html'
    schema = []


class OPATPalliative(OPATPatientList, TaggedPatientList):
    display_name = 'OPAT Palliative'
    direct_add = True
    tag = 'opat_palliative'
    template_name = 'opat_episode_list.html'
    schema = []
