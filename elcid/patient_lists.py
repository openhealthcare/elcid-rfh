from collections import defaultdict

from opal.utils import AbstractBase
from opal.core.patient_lists import TaggedPatientList
from elcid import models
from opal import models as omodels
from opal.core.subrecords import patient_subrecords, episode_subrecords
from intrahospital_api.models import InitialPatientLoad

PATIENT_LIST_SUBRECORDS = [
    models.PrimaryDiagnosis,
    models.Demographics,
    models.Antimicrobial,
    models.Diagnosis,
    models.Location,
    omodels.Tagging,
    InitialPatientLoad
]


def serialise_subrecords(ids, user, subrecords_to_serialise):
    """
        serialises subrecrods to a dict of
        episode_id/patient_id = [serialised_subrecord]
    """
    if not subrecords_to_serialise:
        return {}

    result = defaultdict(lambda: defaultdict(list))
    if issubclass(subrecords_to_serialise[0], omodels.PatientSubrecord):
        qs_args = dict(patient__in=ids)
        key = "patient_id"
    else:
        qs_args = dict(episode__in=ids)
        key = "episode_id"

    for model in subrecords_to_serialise:
        name = model.get_api_name()
        subrecords = model.objects.filter(**qs_args)

        for related in model._meta.many_to_many:
            subrecords = subrecords.prefetch_related(related.attname)

        for sub in subrecords:
            result[getattr(sub, key)][name].append(sub.to_dict(user))
    return result


def serialised_episode_subrecords(episodes, user, subrecords=None):
    """
        serialises episode subrecords.

        takes in subrecords, a list of models of which only those
        related models will be serialised.

        It will filter those subrecords for EpisodeSubrecords and serialises
        those.
    """

    if not subrecords:
        e_subrecords = episode_subrecords()
    else:  # Get only episode subrecords
        e_subrecords = [i for i in episode_subrecords() if i in subrecords]

    return serialise_subrecords(
        episodes, user, e_subrecords
    )


def serialised_patient_subrecords(episodes, user, subrecords=None):
    """
        serialises patient subrecords.

        takes in subrecords, a list of models of which only those
        related models will be serialised.

        It will filter those subrecords for PatientSubrecords and serialises
        those.
    """
    patient_ids = [i.patient_id for i in episodes]
    if not subrecords:
        p_subrecords = patient_subrecords()
    else: #  Get only the patient subrecords
        p_subrecords = [i for i in patient_subrecords() if i in subrecords]

    return serialise_subrecords(
        patient_ids, user, p_subrecords
    )


def serialised_tagging(episodes, user, subrecords=None):
    """
        Checks if we want to serialise the tagging model and if so
        returns the serialised tagging model, (with history if requested)
    """
    taggings = defaultdict(dict)
    if subrecords is None or omodels.Tagging in subrecords:
        qs = omodels.Tagging.objects.filter(
            episode__in=episodes, archived=False
        )

        for tag in qs:
            if tag.value == 'mine' and tag.user != user:
                continue
            taggings[tag.episode_id][tag.value] = True

    return taggings


def serialised(episodes, user, subrecords=None):
    """
    Return a set of serialised EPISODES.
    """
    patient_subs = serialised_patient_subrecords(
        episodes, user, subrecords=subrecords
    )
    episode_subs = serialised_episode_subrecords(
        episodes, user, subrecords=subrecords
    )
    taggings = serialised_tagging(
        episodes, user, subrecords=subrecords
    )

    serialised = []

    for e in episodes:
        d = e.to_dict(user, shallow=True)

        if e.id in episode_subs:
            for key, value in list(episode_subs[e.id].items()):
                d[key] = value

        if e.patient_id in patient_subs:
            for key, value in list(patient_subs[e.patient_id].items()):
                d[key] = value

        if taggings:
            d[omodels.Tagging.get_api_name()] = [taggings[e.id]]
            d[omodels.Tagging.get_api_name()][0]['id'] = e.id
        serialised.append(d)
    return serialised


class RfhPatientList(TaggedPatientList, AbstractBase):
    comparator_service = "EpisodeAddedComparator"

    def to_dict(self, user):
        qs = super(RfhPatientList, self).get_queryset()
        return serialised(qs, user, subrecords=PATIENT_LIST_SUBRECORDS)


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
