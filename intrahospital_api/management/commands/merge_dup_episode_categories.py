from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from opal.models import Patient
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api import logger, merge_patient
from elcid.utils import timing


import os
from intrahospital_api import merge_patient
from opal import models as opal_models
from django.db import transaction
from django.db.models import Count
import reversion
from elcid.utils import timing

DELETE_FILE = "deleted_episodes.txt"


def update_singleton(subrecord_cls, old_parent, new_parent):
    if new_parent.__class__ == opal_models.Episode:
        is_episode_subrecord = True
    else:
        is_episode_subrecord = False

    if is_episode_subrecord:
        old_singleton = subrecord_cls.objects.get(episode=old_parent)
        new_singleton = subrecord_cls.objects.get(episode=new_parent)
    else:
        old_singleton = subrecord_cls.objects.get(patient=old_parent)
        new_singleton = subrecord_cls.objects.get(patient=new_parent)
    if not old_singleton.updated:
        # the old singleton was never editted, we can skip
        return
    if not new_singleton.updated:
        # the new singleton was never editted, we can delete
        # it and replace it with the old one.
        new_singleton.delete()
        if is_episode_subrecord:
            old_singleton.episode = new_parent
        else:
            old_singleton.patient = new_parent
        with reversion.create_revision():
            old_singleton.save()
    else:
        if new_singleton.updated < old_singleton.updated:
            # the old singleton is new than the new singleton
            # stamp the new singleton as reversion
            # then copy over all the fields from the old
            # onto the new
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
            # singleton, then continue with the more recent data
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


def move_non_singletons(subrecord_cls, old_parent, new_parent):
    """
    Moves the old_subrecords query set onto the new parent (a patient or episode).
    In doing so it updates the previous_mrn field to be that of the old_mrn
    """
    if new_parent.__class__ == opal_models.Episode:
        is_episode_subrecord = True
    else:
        is_episode_subrecord = False
    if is_episode_subrecord:
        old_subrecords = subrecord_cls.objects.filter(episode=old_parent)
    else:
        old_subrecords = subrecord_cls.objects.filter(patient=old_parent)
    for old_subrecord in old_subrecords:
        if is_episode_subrecord:
            old_subrecord.episode = new_parent
        else:
            old_subrecord.patient = new_parent
        with reversion.create_revision():
            old_subrecord.save()


def move_record(subrecord_cls, old_parent, new_parent):
    if getattr(subrecord_cls, "_is_singleton", False):
        update_singleton(subrecord_cls, old_parent, new_parent)
    else:
        move_non_singletons(subrecord_cls, old_parent, new_parent)


def merge_episode(*, old_episode, new_episode):
    for episode_related_model in merge_patient.EPISODE_RELATED_MODELS:
        move_record(
            episode_related_model,
            old_episode,
            new_episode,
        )

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
                merge_patient.update_tagging(category_episode, root)
                merge_episode(old_episode=category_episode, new_episode=root)
                category_episode_id = category_episode.id
                patient_id = category_episode.patient_id
                category_episode.delete()
                with open(DELETE_FILE, 'a') as w:
                    w.write(f'\n{patient_id},{category_episode_id}')


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
