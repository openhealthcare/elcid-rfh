"""
Loads a list of patients from a json file.

Creates the patients if they don't exist.
Creates IPC Status for them all.
"""
import json
import datetime
from plugins.ipc.models import IPCStatus
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management.base import BaseCommand
from opal.models import Patient
from plugins.ipc import episode_categories
from intrahospital_api.loader import create_rfh_patient_from_hospital_number
from elcid import episode_categories as infection_episode_categories
from django.db import transaction


def to_date(some_field):
    if some_field:
        return datetime.datetime.strptime(
            some_field, "%d/%m/%Y"
        ).date()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('file_name')

    @transaction.atomic
    def handle(self, file_name, *args, **options):
        no_hospital_number = 0
        created_patients = 0
        created_episodes = 0
        ohc = User.objects.filter(username='ohc').first()
        with open(file_name) as f:
            rows = json.load(f)
        for row in rows:
            if not row["hospital_number"]:
                no_hospital_number += 1
                continue
            demographics_fields = [
                "hospital_number",
                "first_name",
                "surname",
                "nhs_number"
            ]
            demographics = {
                i: row[i] for i in demographics_fields if row.get(i)
            }
            if row["date_of_birth"]:
                demographics["date_of_birth"] = to_date(row["date_of_birth"])

            patient = Patient.objects.filter(
                demographics__hospital_number=row["hospital_number"]
            ).first()

            if not patient:
                patient = create_rfh_patient_from_hospital_number(
                    row["hospital_number"], infection_episode_categories.InfectionService
                )
                patient.demographics_set.update(**demographics)
                created_patients += 1

            episode, created = patient.episode_set.get_or_create(
                category_name=episode_categories.IPCEpisode.display_name
            )
            if created:
                created_episodes += 1
            ipc_status = episode.ipcstatus_set.get()
            ipc_status.comments = row["comments"]
            if not ipc_status.created:
                ipc_status.created = timezone.now()
                ipc_status.created_by = ohc

            fields_to_ignore = set(demographics_fields + ["comments", "date_of_birth"])
            model_fields = set(i.name for i in IPCStatus._meta.get_fields())
            for k, v in row.items():
                if k in fields_to_ignore:
                    continue
                field = k.lower().replace(" ", "_").replace("-", "_")
                date_field = f"{field}_date"
                date_value = to_date(v)
                if field not in model_fields or date_field not in model_fields:
                    if k.startswith("other:"):
                        other_disease = k.split('other:', 1)[-1].strip()
                        setattr(ipc_status, 'other', other_disease)
                        setattr(ipc_status, 'other_date', to_date(v))
                setattr(ipc_status, field, True)
                setattr(ipc_status, date_field, date_value)
            ipc_status.save()
        print(f'Skipped because of no hospital number: {no_hospital_number}')
        print(f'Created patients: {created_patients}')
        print(f'Created episodes: {created_episodes}')
