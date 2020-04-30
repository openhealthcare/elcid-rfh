import datetime
from collections import defaultdict
from django.utils import timezone
from opal.utils import AbstractBase
from opal.core.patient_lists import TaggedPatientList, PatientList
from elcid import models
from plugins.labtests.models import Observation
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
    order = 50

    def to_dict(self, user):
        qs = super(RfhPatientList, self).get_queryset()
        return serialize(qs, user, subrecords=PATIENT_LIST_SUBRECORDS)


class Hepatology(RfhPatientList, TaggedPatientList):
    display_name = 'Hepatology'
    direct_add = True
    tag = 'hepatology'
    template_name = 'episode_list.html'
    schema = []


class Virology(RfhPatientList, TaggedPatientList):
    display_name = 'Virology'
    direct_add = True
    tag = 'viroloy'
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
    display_name = 'Chronic Antifungal'
    order = 15
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
    display_name = 'ICU South'
    direct_add = True
    order = 1
    tag = "icu"
    template_name = 'episode_list.html'
    schema = []


class ICUEast(RfhPatientList, TaggedPatientList):
    display_name = 'ICU East'
    direct_add = True
    order = 2
    tag = "icu_east"
    template_name = 'episode_list.html'
    schema = []


class ICUWest(RfhPatientList, TaggedPatientList):
    display_name = 'ICU West'
    direct_add = True
    order = 3
    tag = "icu_west"
    template_name = 'episode_list.html'
    schema = []


class ICUSHDU(RfhPatientList, TaggedPatientList):
    display_name = 'ICU SHDU'
    direct_add = True
    order = 4
    tag = "icu_shdu"
    template_name = 'episode_list.html'
    schema = []


class NonCanonicalICU(RfhPatientList, TaggedPatientList):
    display_name = 'Non-Canonical ICU'
    direct_add = True
    order = 5
    tag = "non_canonical_icu"
    template_name = 'episode_list.html'
    schema = []


class Covid19NonICU(RfhPatientList, TaggedPatientList):
    display_name = 'Covid 19 Non-ICU'
    direct_add = True
    order = 6
    tag = "covid_19_non_icu"
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
    order = -5
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
    display_name = "Acute Antifungal"
    template_name = 'episode_list.html'
    schema = []
    order = 15

    # if the users can add/remove patients from this list
    is_read_only = True

    @property
    def queryset(self):
        episodes = models.ChronicAntifungal.antifungal_episodes()
        patient_id_to_episode_ids = defaultdict(list)

        for episode in episodes:
            patient_id_to_episode_ids[episode.patient_id].append(episode.id)

        to_remove = set()
        for patient_id, episode_ids in patient_id_to_episode_ids.items():
            if len(episode_ids) > 1:
                old_episodes = sorted(episode_ids, reverse=True)[1:]
                to_remove = to_remove.union(old_episodes)
        return episodes.exclude(id__in=to_remove)


class OrganismPatientlist(AbstractBase):
    is_read_only = True
    schema = []
    template_name = 'episode_list.html'
    organism_list = True

    def four_months_ago(self):
        return timezone.now() - datetime.timedelta(120)

    def get_observations(self):
        return Observation.objects.filter(
            test__test_name__iexact='BLOOD CULTURE'
        ).filter(
            observation_name__iexact='Blood Culture'
        ).filter(
            test__datetime_ordered__gte=self.four_months_ago()
        )

    @property
    def queryset(self):
        obs = self.get_observations()
        qs = omodels.Episode.objects.all()
        return qs.filter(
            patient__lab_tests__observation__in=obs
        ).distinct()


class CandidaList(OrganismPatientlist, RfhPatientList, PatientList):
    display_name = 'Candida'

    def get_observations(self):
        qs = super().get_observations()
        qs = qs.filter(
            observation_value__icontains='candida'
        )
        to_ignore_strings = [
            "Candida auris NOT isolated",
            "Candida NOT isolated",
        ]

        for to_ignore in to_ignore_strings:
            qs = qs.exclude(observation_value__icontains=to_ignore)
        return qs


class StaphAureusList(OrganismPatientlist, RfhPatientList, PatientList):
    display_name = 'Staphylococcus aureus'

    def get_observations(self):
        qs = super().get_observations()
        qs = qs.filter(
            observation_value__icontains='aureus'
        )
        return qs


class EcoliList(OrganismPatientlist, RfhPatientList, PatientList):
    display_name = 'E coli'

    def get_observations(self):
        qs = super().get_observations()
        # regex to match the word as there are a bunch of false positives
        # e.g. Colistin
        qs = qs.filter(
            observation_value__iregex='\y{}\y'.format("coli")
        )
        return qs
