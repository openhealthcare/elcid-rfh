"""
A management command that is run by a cron job
to run intrahospital_api.update_demographics.update_all_patient_information
"""
import time
from django.utils import timezone
from django.core.management.base import BaseCommand
from intrahospital_api.update_demographics import update_all_patient_information
from elcid.constants import DEMOGRAPHICS_SYNC_TIME
from elcid.models import MasterFileMeta
from plugins.monitoring.models import Fact


class Command(BaseCommand):
    help = "Syncs all demographics with the Cerner upstream"

    def handle(self, *args, **options):
        start = time.time()
        before_patient_id_to_insert_date = dict(
            MasterFileMeta.objects.values_list("patient_id", "insert_date", flat=True)
        )
        before_patient_id_to_last_updated = dict(
            MasterFileMeta.objects.values_list("patient_id", "last_updated", flat=True)
        )
        update_all_patient_information()
        end = time.time()

        after_patient_id_to_insert_date = dict(
            MasterFileMeta.objects.values_list("patient_id", "insert_date", flat=True)
        )
        after_patient_id_to_last_updated = dict(
            MasterFileMeta.objects.values_list("patient_id", "last_updated", flat=True)
        )
        updated_cnt = 0
        for patient_id, after_insert_date in after_patient_id_to_insert_date.items():
            after_last_updated = after_patient_id_to_last_updated[patient_id]

            before_insert_date = before_patient_id_to_insert_date.get(patient_id)
            before_last_updated = before_patient_id_to_last_updated.get(patient_id)

            if not after_insert_date == before_insert_date:
                updated_cnt += 1
            elif not after_last_updated == before_last_updated:
                updated_cnt += 1

        now = timezone.now()
        Fact.objects.create(
            when=now, label=DEMOGRAPHICS_SYNC_TIME, value_int=(end-start)/60
        )
        Fact.objects.create(
            when=now, label=updated_cnt, value_int=updated_cnt
        )
