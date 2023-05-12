import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from opal.core.serialization import OpalSerializer
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api import logger, merge_patient
from elcid.utils import timing
from intrahospital_api import merge_patient
from opal import models as opal_models
from django.db import transaction
from django.db.models import Count
import reversion
from elcid.utils import timing

DELETE_FILE = "deleted_episodes.txt"


def update_singleton(subrecord_cls, old_episode, new_episode):
    old_singleton = subrecord_cls.objects.get(episode=old_episode)
    new_singleton = subrecord_cls.objects.get(episode=new_episode)

    if not old_singleton.updated:
        # the old singleton was never editted, we can skip
        return
    if not new_singleton.updated:
        # the new singleton was never editted, we can delete
        # it and replace it with the old one.
        new_singleton.delete()
        old_singleton.episode = new_episode
        with reversion.create_revision():
            old_singleton.save()
    else:
        if new_singleton.updated < old_singleton.updated:
            # the old singleton is newer than the new singleton
            # copy over the fields from the old to the new
            # and save with reversion history
            for field in old_singleton._meta.get_fields():
                field_name = field.name
                if field_name in merge_patient.IGNORED_FIELDS:
                    continue
                setattr(new_singleton, field_name, getattr(old_singleton, field_name))
            with reversion.create_revision():
                new_singleton.save()
        else:
            # the old singleton is older than the new singleton
            # create a reversion record with the data of the old
            # singleton data, then continue with the more recent data
            more_recent_data = {}
            for field in new_singleton._meta.get_fields():
                field_name = field.name
                if field_name in merge_patient.IGNORED_FIELDS:
                    continue
                more_recent_data[field_name] = getattr(new_singleton, field_name)
                setattr(new_singleton, field_name, getattr(old_singleton, field_name))
            new_singleton.save()
            for field, value in more_recent_data.items():
                setattr(new_singleton, field, value)
            with reversion.create_revision():
                new_singleton.save()


def move_non_singletons(subrecord_cls, old_episode, new_episode):
    """
    Updates the old_subrecords queryset to point to the new episode.
    """
    if new_episode.__class__ == opal_models.Episode:
        is_episode_subrecord = True
    else:
        is_episode_subrecord = False
    if is_episode_subrecord:
        old_subrecords = subrecord_cls.objects.filter(episode=old_episode)
    else:
        old_subrecords = subrecord_cls.objects.filter(patient=old_episode)
    for old_subrecord in old_subrecords:
        if is_episode_subrecord:
            old_subrecord.episode = new_episode
        else:
            old_subrecord.patient = new_episode
        with reversion.create_revision():
            old_subrecord.save()


def merge_episode(*, old_episode, new_episode):
    for episode_related_model in merge_patient.EPISODE_RELATED_MODELS:
        if getattr(episode_related_model, "_is_singleton", False):
            update_singleton(episode_related_model, old_episode, new_episode)
        else:
            move_non_singletons(episode_related_model, old_episode, new_episode)


@transaction.atomic
def merge_patient_episodes(patient_id):
    patient = opal_models.Patient.objects.get(id=patient_id)
    episodes = patient.episode_set.all()
    category_names = list(set([i.category_name for i in episodes]))
    for category in category_names:
        category_episodes = [i for i in episodes if i.category_name==category]
        if len(category_episodes) > 1:
            root = category_episodes[0]
            for category_episode in category_episodes[1:]:
                merge_patient.update_tagging(old_episode=category_episode, new_episode=root)
                ohc = User.objects.get(username='ohc')
                prior_json = json.dumps(category_episode.to_dict(ohc), indent=4, cls=OpalSerializer)
                merge_episode(old_episode=category_episode, new_episode=root)
                patient_id = category_episode.patient_id
                category_episode.delete()
                with open(DELETE_FILE, 'a+') as w:
                    w.write(f'{prior_json}\n')


def patient_ids_with_duplicate_episode_categories():
    dups = opal_models.Episode.objects.values('patient_id', 'category_name').annotate(
        cnt=Count('id')
    ).filter(cnt__gte=2)
    return [i["patient_id"] for i in dups]


class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        dups = patient_ids_with_duplicate_episode_categories()
        logger.info(f'Looking at {len(dups)}')
        for idx, patient_id in enumerate(dups):
            logger.info(f'Merging {patient_id} ({idx+1}/{len(dups)})')
            merge_patient_episodes(patient_id)
