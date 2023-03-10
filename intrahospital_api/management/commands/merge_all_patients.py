from django.core.management.base import BaseCommand
from django.utils import timezone
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api import update_demographics
from elcid.utils import timing
from elcid import models as elcid_models
from elcid import episode_categories as elcid_episode_categories
from opal.models import Patient
from intrahospital_api import logger, loader, merge_patient


def get_all_active_merged_patients():
    api = ProdAPI()
    query = """
    SELECT Patient_Number FROM CRS_Patient_Masterfile
    WHERE MERGED = 'Y'
    AND ACTIVE_INACTIVE = 'ACTIVE'
    """
    return [i["Patient_Number"] for i in api.execute_hospital_query(query) if i["Patient_Number"]]


@timing
def get_merge_graph():
    mrns = get_all_active_merged_patients()
    result = []
    errors = []
    cache = update_demographics.create_cache()
    for idx, mrn in enumerate(mrns):
        if idx % 100 == 0:
            print(idx)
        try:
            result.append(update_demographics.get_active_mrn_and_merged_mrn_data(mrn, cache))
        except update_demographics.MergeException:
            errors.append(mrn)
    return result, errors


def process_merged_mrns():
    logger.info('Processing merges')
    logger.info('Caculating merge graph')
    merge_graph, _ = get_merge_graph()
    now = timezone.now()

    logger.info('Generating MRN to patient map')
    demographics = elcid_models.Demographics.objects.all().select_related('patient')
    mrn_to_patient = {i.hospital_number: i.patient for i in demographics}
    logger.info('Generating merged MRNs')
    to_create = []
    for active_mrn, merged_dicts in merge_graph:
        merged_mrns = [i["mrn"] for i in merged_dicts]
        active_patient = mrn_to_patient.get(active_mrn)
        merged_mrn_objs = elcid_models.MergedMRN.objects.filter(
            mrn__in=merged_mrns
        )
        unmerged_patients = Patient.objects.filter(
            demographics__hospital_number__in=merged_mrns
        )
        unmerged_patients = [
            mrn_to_patient.get(i) for i in merged_mrns if i in mrn_to_patient
        ]
        if len(unmerged_patients) > 0:
            if not active_patient:
                active_patient, _ = loader.get_or_create_patient(
                    active_mrn,
                    elcid_episode_categories.InfectionService,
                    run_async=False
                )
            for unmerged_patient in unmerged_patients:
                if active_patient:
                    merge_patient.merge_patient(
                        old_patient=unmerged_patient,
                        new_patient=active_patient
                    )
        if active_patient:
            existing_merged_mrns_and_comments_to_merged_mrn = {(i.mrn, i.merge_comments,): i for i in merged_mrn_objs}
            new_merged_mrn_and_comments_to_merged_mrn_dict = {(i["mrn"], i["merge_comments"]): i for i in merged_dicts}

            new_keys = set(new_merged_mrn_and_comments_to_merged_mrn_dict.keys())
            old_keys = set(existing_merged_mrns_and_comments_to_merged_mrn.keys())

            to_remove_keys = list(old_keys - new_keys)

            for mrn_and_comments in to_remove_keys:
                existing_merged_mrns_and_comments_to_merged_mrn[mrn_and_comments].delete()

            to_add_keys = list(new_keys - old_keys)

            for mrn_and_comments in to_add_keys:
                new_merged_dict = new_merged_mrn_and_comments_to_merged_mrn_dict[mrn_and_comments]
                to_create.append(
                    elcid_models.MergedMRN(
                        patient=active_patient, our_merge_datetime=now, **new_merged_dict
                    )
                )
    logger.info('Saving merged MRNs')
    elcid_models.MergedMRN.objects.bulk_create(to_create)



class Command(BaseCommand):
    def handle(self, *args, **options):
        process_merged_mrns()
