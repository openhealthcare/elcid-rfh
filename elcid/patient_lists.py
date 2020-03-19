from opal.utils import AbstractBase
from opal.core.patient_lists import TaggedPatientList
from elcid import models
from opal import models as omodels
from intrahospital_api.models import InitialPatientLoad
from elcid.episode_serialization import serialize

PATIENT_LIST_SUBRECORDS = [
    models.PrimaryDiagnosis,
    models.Demographics,
    models.Antimicrobial,
    models.Diagnosis,
    models.Location,
    omodels.Tagging,
    InitialPatientLoad
]


class RfhPatientList(TaggedPatientList, AbstractBase):
    comparator_service = "EpisodeAddedComparator"
    order = 50

    def to_dict(self, user):
        qs = super(RfhPatientList, self).get_queryset()
        return serialize(qs, user, subrecords=PATIENT_LIST_SUBRECORDS)


class Hepatology(RfhPatientList):
    display_name = 'Hepatology'
    direct_add = True
    tag = 'hepatology'
    template_name = 'episode_list.html'
    schema = []


class SurgicalAntibioti(RfhPatientList):
    display_name = 'Surgical Antibiotic Stewardship Round'
    direct_add = True
    tag = 'sasr'
    template_name = 'episode_list.html'
    schema = []


class MAU(RfhPatientList):
    display_name = 'MAU Round'
    direct_add = True
    tag = 'mau'
    template_name = 'episode_list.html'
    schema = []


class Antifungal(RfhPatientList):
    display_name = 'Antifungal Stewardship'
    order = -5
    direct_add = True
    tag = 'antifungal'
    template_name = 'episode_list.html'
    schema = []


class RnohWardround(RfhPatientList):
    display_name = 'RNOH Ward Round'
    direct_add = True
    tag = "rnoh_wardround"
    template_name = 'episode_list.html'
    schema = []


class CDIFF(RfhPatientList):
    display_name = 'CDIFF Round'
    direct_add = True
    tag = "cdiff_wardround"
    template_name = 'episode_list.html'
    schema = []


class ICU(RfhPatientList):
    display_name = 'ICU West'
    direct_add = True
    order = 1
    tag = "icu"
    template_name = 'episode_list.html'
    schema = []


class ICUEast(RfhPatientList):
    display_name = 'ICU East'
    direct_add = True
    order = 2
    tag = "icu_east"
    template_name = 'episode_list.html'
    schema = []


class ICUNorth(RfhPatientList):
    display_name = 'ICU North'
    direct_add = True
    order = 3
    tag = "icu_north"
    template_name = 'episode_list.html'
    schema = []


class ICUSHDU(RfhPatientList):
    display_name = 'ICU SHDU'
    direct_add = True
    order = 4
    tag = "icu_shdu"
    template_name = 'episode_list.html'
    schema = []


class Covid19NonICU(RfhPatientList):
    display_name = 'Covid 19 Non-ICU'
    direct_add = True
    order = 5
    tag = "covid_19_non_icu"
    template_name = 'episode_list.html'
    schema = []


class Acute(RfhPatientList):
    display_name = 'Acute'
    direct_add = True
    tag = "acute"
    template_name = 'episode_list.html'
    schema = []


class Chronic(RfhPatientList):
    display_name = 'Chronic Infections'
    direct_add = True
    tag = "chronic"
    template_name = 'episode_list.html'
    schema = []


class Haematology(RfhPatientList):
    display_name = 'Haematology'
    direct_add = True
    tag = "haem"
    template_name = 'episode_list.html'
    schema = []


class HIV(RfhPatientList):
    display_name = 'HIV'
    direct_add = True
    tag = "hiv"
    template_name = 'episode_list.html'
    schema = []


class Paediatric(RfhPatientList):
    display_name = 'Paediatric'
    direct_add = True
    tag = "paediatric"
    template_name = 'episode_list.html'
    schema = []


class MalboroughClinic(RfhPatientList):
    display_name = 'Malborough Clinic'
    direct_add = True
    tag = "malborough"
    template_name = 'episode_list.html'
    schema = []


class Renal(RfhPatientList):
    display_name = 'Renal'
    order = -5
    direct_add = True
    tag = "renal"
    template_name = 'episode_list.html'
    schema = []


class Sepsis(RfhPatientList):
    display_name = 'Sepsis Pathway'
    direct_add = True
    tag = "sepsis"
    template_name = 'episode_list.html'
    schema = []


class Bacteraemia(RfhPatientList):
    display_name = 'Bacteraemia'
    direct_add = True
    tag = "bacteraemia"
    template_name = 'episode_list.html'
    schema = []
    order = -10


class PCP(RfhPatientList):
    display_name = 'PCP'
    direct_add = True
    tag = "pcp"
    template_name = 'episode_list.html'
    schema = []


class R1(RfhPatientList):
    display_name = 'R1'
    direct_add = True
    tag = "r1"
    template_name = 'episode_list.html'
    schema = []


class LiverTransplantation(RfhPatientList):
    display_name = 'Liver Transplantation'
    direct_add = True
    tag = "liver_transplantation"
    template_name = 'episode_list.html'
    schema = []
