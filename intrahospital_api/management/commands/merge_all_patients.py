"""
A management command that will be called once to create all
"""
from django.core.management.base import BaseCommand
from intrahospital_api import update_demographics
from elcid import models as elcid_models
from opal.models import Patient


def get_queryset():
    patients = Patient.objects.filter(masterfilemeta__merged="Y")
    if patients.filter(masterfilemeta__active_inactive="INACTIVE").exists():
        raise ValueError("Unexpected inactive patients")
    return patients.prefetch_related("demographics_set")


class Command(BaseCommand):
    def handle(self, *args, **options):
        qs = get_queryset()
        merged_mrns = []
        for patient in qs:
            mrn = patient.demographics_set.all()[0].hospital_number
            (
                active_mrn,
                merge_results,
            ) = update_demographics.get_active_mrn_and_merged_mrn_data(mrn)
            if not active_mrn == mrn:
                raise ValueError(
                    f" ".join([
                        f"For some reason the active mrn {active_mrn}",
                        f"is not the same as the mrn {mrn}"
                    ])
                )
            for merge_result in merge_results:
                merged_mrn = elcid_models.MergedMRN(patient=patient)
                for k, v in merge_result.items():
                    setattr(merged_mrn, k, v)
                merged_mrns.append(merged_mrn)
        elcid_models.MergedMRN.objects.bulk_create(merged_mrns)
