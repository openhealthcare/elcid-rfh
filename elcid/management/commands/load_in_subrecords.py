import json, os

from django.contrib.auth import get_user_model

from django.core.management.base import BaseCommand

from opal.models import Patient, PatientSubrecord
from opal.core import subrecords

from lab.models import LabTest


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'filename', help="the file name to load from"
        )
        parser.add_argument(
            'user', help="the username who is doing the update"
        )
        parser.add_argument(
            '--patient', help="attribute all subrecords to a ", type=int
        )

    def rewrite_ids(self, patient_data, patient, episode=None):
        """ make sure the patient id is correct and the
            episode ids match to episodes from that patient
        """
        existing_episodes = patient.episode_set.values_list("id", flat=True)

        for subrecord_name, subrecord_dicts in patient_data.items():
            subrecord = subrecords.get_subrecord_from_api_name(subrecord_name)
            if issubclass(subrecord, PatientSubrecord):
                # make sure the patient id is our patient
                for subrecord_dict in subrecord_dicts:
                    subrecord_dict['patient_id'] = patient.id
                    # if it has an id and its not our patient, nuke it
                    if 'id' in subrecord_dict:
                        if not subrecord.objects.filter(
                            patient=patient,
                            id=subrecord_dict["id"]
                        ).exists():
                            del subrecord_dict['id']
            else:
                for subrecord_dict in subrecord_dicts:
                    # if its got an episode id and its not one of ours
                    # nuke it
                    if subrecord_dicts['episode_id'] not in existing_episodes:
                        del subrecord_dicts['episode_id']
                    if 'id' in subrecord_dict:
                        # if its got an id and its not one of ours, nuke it
                        if not subrecord.objects.filter(
                            episode__in=existing_episodes,
                            id=subrecord_dict["id"]
                        ).exists():
                            del subrecord_dict['id']

    def handle(self, *args, **options):
        file_name = options['filename']
        if not os.path.exists(file_name):
            raise ValueError("unable to find {}".format(file_name))

        patient_data = json.loads(open(file_name, 'r').read())
        patient_id = options.get('patient')
        patient_qs = Patient.objects.none()
        hospital_number = None
        user = get_user_model().objects.get(username=options['user'])

        if "demogaphics" in patient_data:
            hospital_number = patient_data["demographics"]["hospital_number"]
            patient_qs = Patient.objects.filter(
                demographics__hospital_number=hospital_number
            )

        # if they've pass in a patient id that does not exist
        if patient_id and not Patient.objects.filter(id=patient_id).exists():
            err = "Patient id {} does not exist".format(patient_id)
            raise ValueError(err.format(patient_id))

        # if they've passed in a patient id a demographics with
        # a hospital number but that hospital number is in use
        # with a different patient then raise.
        if patient_id and patient_qs.exists() and not patient_qs.filter(
            id=patient_id
        ).exists():
            err = "The hospital number {0} is currently in use by {1} so can "
            err = err + "not be assigned to {2}"
            raise ValueError(
                err.format(hospital_number, patient_qs.first().id, patient_id)
            )

        # if they haven't passed in a patient number or a demographics
        # with a hospital number then raise.
        if not patient_id and not hospital_number:
            err = "We require a hospital number or a patient id to add a parient"
            raise ValueError(err)

        # if they've passed in a hospital number in demographics use
        # that patient
        if hospital_number:
            if not patient_qs.exists():
                patient = Patient.objects.create()
            else:
                patient = patient_qs.first()
                self.rewrite_ids(patient_data, patient)
                patient.bulk_update(
                    patient_data, user, force=True
                )
        else:
            # if they've passed in a patient id then override all patient
            # subrecords to use that id, and all episodes to be the
            # latest of that patients episodes (this is should not be used casually)
            patient = Patient.objects.get(id=patient_id)
            self.rewrite_ids(patient_data, patient)
            patient.bulk_update(
                patient_data, user, force=True
            )
