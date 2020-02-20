import datetime
from collections import defaultdict
from opal.utils import AbstractBase
from opal.core.patient_lists import TaggedPatientList, PatientList
from elcid import models
from opal import models as omodels
from intrahospital_api.models import InitialPatientLoad
from elcid.episode_serialization import serialize
from elcid.episode_categories import InfectionService

PATIENT_LIST_SUBRECORDS = [
    models.PrimaryDiagnosis,
    models.Demographics,
    models.Antimicrobial,
    models.Diagnosis,
    models.Location,
    models.ChronicAntifungal,
    omodels.Tagging,
    InitialPatientLoad
]


class RfhPatientList(AbstractBase):
    comparator_service = "EpisodeAddedComparator"

    def to_dict(self, user):
        qs = super(RfhPatientList, self).get_queryset()
        return serialize(qs, user, subrecords=PATIENT_LIST_SUBRECORDS)


class Hepatology(RfhPatientList, TaggedPatientList):
    display_name = 'Hepatology'
    direct_add = True
    tag = 'hepatology'
    template_name = 'episode_list.html'
    schema = []


class SurgicalAntibioti(RfhPatientList, TaggedPatientList):
    display_name = 'Surgical Antibiotic Stewardship Round'
    direct_add = True
    tag = 'sasr'
    template_name = 'episode_list.html'
    schema = []


class MAU(RfhPatientList, TaggedPatientList):
    display_name = 'MAU Round'
    direct_add = True
    tag = 'mau'
    template_name = 'episode_list.html'
    schema = []


class Antifungal(RfhPatientList, TaggedPatientList):
    display_name = 'Antifungal Stewardship'
    direct_add = True
    tag = 'antifungal'
    template_name = 'episode_list.html'
    schema = []


class RnohWardround(RfhPatientList, TaggedPatientList):
    display_name = 'RNOH Ward Round'
    direct_add = True
    tag = "rnoh_wardround"
    template_name = 'episode_list.html'
    schema = []


class CDIFF(RfhPatientList, TaggedPatientList):
    display_name = 'CDIFF Round'
    direct_add = True
    tag = "cdiff_wardround"
    template_name = 'episode_list.html'
    schema = []


class ICU(RfhPatientList, TaggedPatientList):
    display_name = 'ICU'
    direct_add = True
    tag = "icu"
    template_name = 'episode_list.html'
    schema = []


class Acute(RfhPatientList, TaggedPatientList):
    display_name = 'Acute'
    direct_add = True
    tag = "acute"
    template_name = 'episode_list.html'
    schema = []


class Chronic(RfhPatientList, TaggedPatientList):
    display_name = 'Chronic Infections'
    direct_add = True
    tag = "chronic"
    template_name = 'episode_list.html'
    schema = []


class Haematology(RfhPatientList, TaggedPatientList):
    display_name = 'Haematology'
    direct_add = True
    tag = "haem"
    template_name = 'episode_list.html'
    schema = []


class HIV(RfhPatientList, TaggedPatientList):
    display_name = 'HIV'
    direct_add = True
    tag = "hiv"
    template_name = 'episode_list.html'
    schema = []


class Paediatric(RfhPatientList, TaggedPatientList):
    display_name = 'Paediatric'
    direct_add = True
    tag = "paediatric"
    template_name = 'episode_list.html'
    schema = []


class MalboroughClinic(RfhPatientList, TaggedPatientList):
    display_name = 'Malborough Clinic'
    direct_add = True
    tag = "malborough"
    template_name = 'episode_list.html'
    schema = []


class Renal(RfhPatientList, TaggedPatientList):
    display_name = 'Renal'
    direct_add = True
    tag = "renal"
    template_name = 'episode_list.html'
    schema = []


class Sepsis(RfhPatientList, TaggedPatientList):
    display_name = 'Sepsis Pathway'
    direct_add = True
    tag = "sepsis"
    template_name = 'episode_list.html'
    schema = []


class Bacteraemia(RfhPatientList, TaggedPatientList):
    display_name = 'Bacteraemia'
    direct_add = True
    tag = "bacteraemia"
    template_name = 'episode_list.html'
    schema = []
    order = -10


class PCP(RfhPatientList, TaggedPatientList):
    display_name = 'PCP'
    direct_add = True
    tag = "pcp"
    template_name = 'episode_list.html'
    schema = []


class R1(RfhPatientList, TaggedPatientList):
    display_name = 'R1'
    direct_add = True
    tag = "r1"
    template_name = 'episode_list.html'
    schema = []


class LiverTransplantation(RfhPatientList, TaggedPatientList):
    display_name = 'Liver Transplantation'
    direct_add = True
    tag = "liver_transplantation"
    template_name = 'episode_list.html'
    schema = []


class ChronicAntifungal(RfhPatientList, PatientList):
    display_name = "Chronic Antifungal"
    template_name = 'episode_list.html'
    schema = []
    is_chronic = True

    @property
    def queryset(self):
        active_from_date = datetime.date.today() - datetime.timedelta(3)
        episodes = omodels.Episode.objects.filter(
            patient__chronicantifungal__updated_dt__gte=active_from_date
        ).filter(
            category_name=InfectionService.display_name
        ).distinct()
        patient_id_to_episode_ids = defaultdict(list)

        for episode in episodes:
            patient_id_to_episode_ids[episode.patient_id].append(episode.id)

        to_remove = set()
        for patient_id, episode_ids in patient_id_to_episode_ids.items():
            if len(episode_ids) > 1:
                old_episodes = sorted(episode_ids, reverse=True)[1:]
                to_remove = to_remove.union(old_episodes)
        return episodes.exclude(id__in=to_remove)

