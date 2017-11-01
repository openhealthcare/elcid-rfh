from opal.utils import AbstractBase
from opal.core.patient_lists import TaggedPatientList
from collections import defaultdict
from opal.core.subrecords import patient_subrecords
from lab.models import LabTest
from opal.models import Episode


class RfhPatientList(TaggedPatientList, AbstractBase):
    comparator_service = "EpisodeAddedComparator"

    def serialise_without_tests(self, user, episodes):
        """
        Return a set of serialised EPISODES.

        If HISTORIC_TAGS is Truthy, return deleted tags as well.
        If EPISODE_HISTORY is Truthy return historic episodes as well.
        """
        patient_ids = [e.patient_id for e in episodes]
        patient_subs = defaultdict(lambda: defaultdict(list))

        episode_subs = Episode.objects.serialised_episode_subrecords(
            episodes, user
        )
        for model in patient_subrecords():
            if model == LabTest:
                continue
            name = model.get_api_name()
            subrecords = model.objects.filter(patient__in=patient_ids)

            for sub in subrecords:
                patient_subs[sub.patient_id][name].append(sub.to_dict(user))

        # We do this here because it's an order of magnitude quicker than
        # hitting episode.tagging_dict() for each episode in a loop.
        taggings = defaultdict(dict)
        from opal.models import Tagging
        qs = Tagging.objects.filter(episode__in=episodes)
        qs = qs.filter(archived=False)

        for tag in qs:
            if tag.value == 'mine' and tag.user != user:
                continue
            taggings[tag.episode_id][tag.value] = True

        serialised = []

        for e in episodes:
            d = e.to_dict(user, shallow=True)

            for key, value in list(episode_subs[e.id].items()):
                d[key] = value
            for key, value in list(patient_subs[e.patient_id].items()):
                d[key] = value

            d['tagging'] = [taggings[e.id]]
            d['tagging'][0]['id'] = e.id
            serialised.append(d)

        return serialised

    def to_dict(self, user):
        return self.serialise_without_tests(user, self.get_queryset(user=user))


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
    display_name = 'ICU'
    direct_add = True
    tag = "icu"
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
    direct_add = True
    tag = "renal"
    template_name = 'episode_list.html'
    schema = []


class TB(RfhPatientList):
    display_name = 'TB'
    direct_add = True
    tag = "tb"
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
