from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from opal.models import Patient
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api import logger, loader, merge_patient, update_demographics
from elcid import episode_categories as elcid_episode_categories
from elcid.utils import timing
from elcid import models


# Returns all active merged patients
# used by the merge_all_patients mgmt
# command
GET_ALL_ACTIVE_MERGED_MRNS = """
    SELECT Patient_Number FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
    AND ACTIVE_INACTIVE = 'ACTIVE'
"""

def get_all_active_merged_mrns():
    api = ProdAPI()
    query_result = api.execute_hospital_query(GET_ALL_ACTIVE_MERGED_MRNS)
    return [i["Patient_Number"] for i in query_result]



def our_merge_patient(*, old_patient, new_patient):
    """
    All elcid native non-singleton entries to be converted to
    the equivalent episode category on the wining MRN, with a reference
    created in the original_mrn field where they have been moved

    Copy teams from the old infection service episode? To the new
    Infection service episode

    Copy over any episode categories that do not exist, iterate
    over subrecord attached to these and add the PreviousMRN

    Singleton entries to pick the latest but create a reversion
    history entry for the non-oldest, with a reference to the original_mrn

    Non-singletons entries are moved from the old parent to the
    new parent.

    This is the same as merge_patient.merge_patient but
    does not call load_patient.
    """
    old_mrn = old_patient.demographics().hospital_number
    for patient_related_model in merge_patient.PATIENT_RELATED_MODELS:
        merge_patient.move_record(
            patient_related_model,
            old_patient,
            new_patient,
            old_mrn,
        )
    for old_episode in old_patient.episode_set.all():
        # Note: if the old episode has multiple episode
        # categories of the same category name
        # this will merge those.
        new_episode, _ = new_patient.episode_set.get_or_create(
            category_name=old_episode.category_name
        )
        merge_patient.update_tagging(old_episode=old_episode, new_episode=new_episode)
        for episode_related_model in merge_patient.EPISODE_RELATED_MODELS:
            merge_patient.move_record(
                episode_related_model,
                old_episode,
                new_episode,
                old_mrn,
            )
    old_patient.delete()
    new_patient.mergedmrn_set.filter(mrn=old_mrn).update(
        our_merge_datetime=timezone.now()
    )
    merge_patient.updates_statuses(new_patient)


@transaction.atomic
def check_and_handle_upstream_merges_for_mrns(mrns):
    """
    Takes in a list of active MRNs.

    Filters those not related to elCID.

    Creates MergedMRNs for the related inactive MRNs
    and merges any elcid patients with inactive MRNs.


    This function looks the same as
    update_demographics.check_and_handle_upstream_merges_for_mrns
    but instead of running merge_patient.merge_patient
    it runs the above merge_patient function that
    does not call load_patient.
    """
    cache = update_demographics.get_mrn_to_upstream_merge_data()
    now = timezone.now()
    active_mrn_to_merged_dicts = {}
    # it is possible that the MRNs passed
    # in will link to the same active MRN
    # so make sure we only have one per
    # active MRN
    for mrn in mrns:
        active_mrn, merged_dicts = update_demographics.get_active_mrn_and_merged_mrn_data(
            mrn, cache
        )
        active_mrn_to_merged_dicts[active_mrn] = merged_dicts

    logger.info('Generating merged MRNs')
    to_create = []
    for active_mrn, merged_dicts in active_mrn_to_merged_dicts.items():
        merged_mrns = [i["mrn"] for i in merged_dicts]
        active_patient = Patient.objects.filter(
            demographics__hospital_number=active_mrn
        ).first()
        merged_mrn_objs = models.MergedMRN.objects.filter(
            mrn__in=merged_mrns
        )
        unmerged_patients = Patient.objects.filter(
            demographics__hospital_number__in=merged_mrns
        )
        # If we have patients that are inactive we need to do a merge.
        if len(unmerged_patients) > 0:
            if not active_patient:
                active_patient, _ = loader.get_or_create_patient(
                    active_mrn,
                    elcid_episode_categories.InfectionService,
                    run_async=False
                )
            for unmerged_patient in unmerged_patients:
                if active_patient:
                    our_merge_patient(
                        old_patient=unmerged_patient,
                        new_patient=active_patient
                    )

        # If there is an active patient then we need to create merged MRNs.
        if active_patient:
            # we don't delete and write anew to preserve the our_merge_datetime field
            existing_merged_mrns = set([i.mrn for i in merged_mrn_objs])
            new_merged_mrns = set(i["mrn"] for i in merged_dicts)
            to_add_merged_mrns = new_merged_mrns - existing_merged_mrns

            for merged_dict in merged_dicts:
                if merged_dict["mrn"] in to_add_merged_mrns:
                    to_create.append(
                        models.MergedMRN(
                            patient=active_patient,
                            our_merge_datetime=now,
                            **merged_dict
                        )
                    )
    logger.info('Saving merged MRNs')
    models.MergedMRN.objects.bulk_create(to_create)
    logger.info(f'Saved {len(to_create)} merged MRNs')


class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        mrns = get_all_active_merged_mrns()
        check_and_handle_upstream_merges_for_mrns(mrns)
