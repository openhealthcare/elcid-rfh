from django.utils import timezone
from elcid import models
from intrahospital_api import loader
from opal.core import subrecords
from django.db import transaction
import reversion

IGNORED_FIELDS = {
    'id', 'episode', 'patient', 'previous_mrn'
}

def update_singleton(old_singleton, new_parent, old_mrn, new_mrn, is_episode_subrecord):
    if is_episode_subrecord:
        new_singleton = old_singleton.__class__.objects.get(episode=new_parent)
    else:
        new_singleton = old_singleton.__class__.objects.get(patient=new_parent)
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
        old_singleton.previous_mrn = old_mrn
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
                if field_name in IGNORED_FIELDS:
                    continue
                setattr(new_singleton, field_name, getattr(old_singleton, field_name))
            new_singleton.previous_mrn = old_mrn
            with reversion.create_revision():
                new_singleton.save()
        else:
            # the old singleton is older than the new singleton
            # create a reversion record with the data of the old
            # singleton, then continue with the more recent data
            more_recent_data = {}
            new_singleton.previous_mrn = old_mrn
            for field in new_singleton._meta.get_fields():
                field_name = field.name
                if field_name in IGNORED_FIELDS:
                    continue
                more_recent_data[field_name] = getattr(new_singleton, field_name)
                setattr(new_singleton, field_name, getattr(old_singleton, field_name))
            with reversion.create_revision():
                new_singleton.save()
            for field, value in more_recent_data.items():
                setattr(new_singleton, field, value)
            new_singleton.previous_mrn = None
            with reversion.create_revision():
                new_singleton.save()

def copy_non_singletons(old_subrecords, new_parent, old_mrn, is_episode_subrecord):
    """
    Copies the old_subrecords query set onto the new parent (a patient or episode).
    In doing so it updates the previous_mrn field to be that of the old_mrn
    """
    for old_subrecord in old_subrecords:
        if is_episode_subrecord:
            old_subrecord.episode = new_parent
        else:
            old_subrecord.patient = new_parent
        old_subrecord.previous_mrn = old_mrn
        with reversion.create_revision():
            old_subrecord.save()


def copy_subrecord(subrecord_cls, old_parent, new_parent, old_mrn, new_mrn, is_episode_subrecord):
    """
    Copies a subrecord_cl from an old parent (a patient or an episode)
    to a new one.
    """
    if is_episode_subrecord:
        qs = subrecord_cls.objects.filter(episode=old_parent)
    else:
        qs = subrecord_cls.objects.filter(patient=old_parent)
    if subrecord_cls._is_singleton:
        update_singleton(qs[0], new_parent, old_mrn, new_mrn, is_episode_subrecord)
    else:
        copy_non_singletons(qs, new_parent, old_mrn, is_episode_subrecord)


@transaction.atomic
def merge_patient(old_patient, new_patient):
    """
    All elcid native non-singleton entries to be converted to
    the equivalent episode category on the wining MRN, with a reference
    created in the original_mrn field where they have been moved

    Copy teams from the old infection service episode? To the new
    Infection service episode

    Copy over any episode categories that do not exist, iterate
    over subrecord attached to these and add the PreviousMRN

    Elcid native singleton entries to pick the latest but create a reversion history entry for the non-oldest, with a reference to the original_mrn
    """
    old_mrn = old_patient.demographics().hospital_number
    new_mrn = new_patient.demographics().hospital_number

    for patient_subrecord in subrecords.patient_subrecords():
        if not issubclass(patient_subrecord, models.PreviousMRN):
            continue
        copy_subrecord(
            patient_subrecord,
            old_patient,
            new_patient,
            old_mrn,
            new_mrn,
            is_episode_subrecord=False
        )
    for old_episode in old_patient.episode_set.all():
        # Note: if the old episode has multiple episode
        # categories of the same category name
        # this will merge those.
        new_episode, _ = new_patient.episode_set.get_or_create(
            category_name=old_episode.category_name
        )
        for episode_subrecord in subrecords.episode_subrecords():
            if not issubclass(episode_subrecord, models.PreviousMRN):
                continue
            copy_subrecord(
                episode_subrecord,
                old_episode,
                new_episode,
                old_mrn,
                new_mrn,
                is_episode_subrecord=True
            )
    old_patient.delete()
    new_patient.mergedmrn_set.filter(mrn=old_mrn).update(
        our_merge_datetime=timezone.now()
    )
    loader.load_patient(new_patient, run_async=False)
