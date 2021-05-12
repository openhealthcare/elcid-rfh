from collections import defaultdict
from opal import managers
from opal import models as omodels
from opal.core.subrecords import patient_subrecords, episode_subrecords


def serialize_subrecords(ids, user, subrecords_to_serialise):
    """
        serialises subrecrods to a dict of
        episode_id/patient_id = [serialize_subrecord]
    """
    if not subrecords_to_serialise:
        return {}

    result = defaultdict(lambda: defaultdict(list))

    # set an empty list for all subrecords that we want to create
    for id in ids:
        for subrecord in subrecords_to_serialise:
            result[id][subrecord.get_api_name()] = []

    if issubclass(subrecords_to_serialise[0], omodels.PatientSubrecord):
        if len(ids) == 1:
            qs_args = {'patient_id': ids[0]}
        else:
            qs_args = {'patient_id__in': ids}

        key = "patient_id"
    else:
        if len(ids) == 1:
            qs_args = {'episode_id': ids[0]}
        else:
            qs_args = {'episode_id__in': ids}

        key = "episode_id"

    for model in subrecords_to_serialise:
        name = model.get_api_name()
        subrecords = managers.prefetch(model.objects.filter(**qs_args))

        for related in model._meta.many_to_many:
            subrecords = subrecords.prefetch_related(related.attname)

        for sub in subrecords:
            result[getattr(sub, key)][name].append(sub.to_dict(user))
    return result


def serialize_episode_subrecords(episodes, user, subrecords=None, categories=None):
    """
        serialises episode subrecords.

        takes in subrecords, a list of models of which only those
        related models will be serialize.

        It will filter those subrecords for EpisodeSubrecords and serialises
        those.
    """

    if not subrecords:
        e_subrecords = list(episode_subrecords())
    else:  # Get only episode subrecords
        if categories:
            e_subrecords = []
            for sub in episode_subrecords():
                if categories:
                    if hasattr(sub, '_category'):
                        if sub._category.display_name in categories:
                            e_subrecords.append(sub)
                    else:
                        e_subrecords.append(sub)
        else:
            e_subrecords = [i for i in episode_subrecords() if i in subrecords]

    return serialize_subrecords(
        [i.id for i in episodes], user, e_subrecords
    )


def serialize_patient_subrecords(episodes, user, subrecords=None, categories=None):
    """
        serialises patient subrecords.

        takes in subrecords, a list of models of which only those
        related models will be serialize.

        It will filter those subrecords for PatientSubrecords and serialises
        those.
    """
    patient_ids = list({i.patient_id for i in episodes})

    if not subrecords:
        p_subrecords = list(patient_subrecords())
    else:  # Get only the patient subrecords
        if categories:
            p_subrecords = []
            for sub in patient_subrecords():
                if categories:
                    if hasattr(sub, '_category'):
                        if sub._category.display_name in categories:
                            p_subrecords.append(sub)
                    else:
                        p_subrecords.append(sub)
        else:
            p_subrecords = [i for i in patient_subrecords() if i in subrecords]

    return serialize_subrecords(
        patient_ids, user, p_subrecords
    )


def serialize_tagging(episodes, user, subrecords=None):
    """
        Checks if we want to serialise the tagging model and if so
        returns the serialize tagging model, (with history if requested)
    """
    if subrecords is None or omodels.Tagging in subrecords:
        taggings = {e.id: dict(id=e.id) for e in episodes}
        qs = omodels.Tagging.objects.filter(
            episode__in=episodes, archived=False
        )

        for tag in qs:
            if tag.value == 'mine' and tag.user != user:
                continue
            taggings[tag.episode_id][tag.value] = True

        return taggings


def serialize(episodes, user, subrecords=None):
    """
    Return a set of serialize EPISODES.
    """
    categories = {e.category_name for e in episodes}

    patient_subs = serialize_patient_subrecords(
        episodes, user, subrecords=subrecords, categories=categories
    )
    episode_subs = serialize_episode_subrecords(
        episodes, user, subrecords=subrecords, categories=categories
    )
    taggings = serialize_tagging(
        episodes, user, subrecords=subrecords
    )

    serialize = []

    for e in episodes:
        d = e.to_dict(user, shallow=True)

        if e.id in episode_subs:
            for key, value in list(episode_subs[e.id].items()):
                d[key] = value

        if e.patient_id in patient_subs:
            for key, value in list(patient_subs[e.patient_id].items()):
                d[key] = value

        if taggings:
            tagging_dict = taggings[e.id]
            d[omodels.Tagging.get_api_name()] = [tagging_dict]

        serialize.append(d)
    return serialize
