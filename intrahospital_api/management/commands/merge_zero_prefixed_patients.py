from django.core.management.base import BaseCommand
from elcid.models import Demographics
from plugins.dischargesummary import loader as dicharge_summary_loader
from intrahospital_api import loader
from intrahospital_api import merge_patient
from django.db import transaction
from intrahospital_api import logger
from elcid.utils import timing

@timing
@transaction.atomic
def update_patients_with_leading_zero_with_no_counter_part():
    # patients with leading 0s but no duplicate, remove the 0, re-sync all upstream
    cnt = 0
    demos = Demographics.objects.filter(hospital_number__startswith='0').select_related('patient')
    for demo in demos:
        mrn = demo.hospital_number.lstrip('0')
        if mrn and not Demographics.objects.filter(hospital_number=mrn).exists():
            print(f'Changing stripping the zero from the MRN of patient id {demo.patient_id}')
            demo.hospital_number = mrn
            demo.save()
            cnt += 1
        loader.load_patient(demo.patient, run_async=False)
        dicharge_summary_loader.load_dischargesummaries(demo.patient)
    print(f'updated {cnt} patients who had no non zero')


@timing
@transaction.atomic
def merge_zero_patients():
    demos = Demographics.objects.filter(hospital_number__startswith='0')
    merged = []
    for demo in demos:
        mrn = demo.hospital_number
        # Ignore MRNs with only zeros
        if not mrn.lstrip('0'):
            continue
        to_demos = Demographics.objects.filter(
            hospital_number=mrn.lstrip('0')
        ).first()
        if to_demos:
            from_patient = demo.patient
            to_patient = to_demos.patient
            merge_patient.merge_patient(old_patient=from_patient, new_patient=to_patient)
            merged.append(mrn)
    return merged


class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        update_patients_with_leading_zero_with_no_counter_part()
        merged = merge_zero_patients()
        for merged_mrn in merged:
            logger.info(f"Merged {merged_mrn}")
