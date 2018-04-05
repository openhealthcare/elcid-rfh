from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from opal.core.views import json_response
from opal import models as omodels
from opal.core import subrecords
from lab import models as lmodels
from elcid.patient_lists import serialised


def patient_to_dict(patient, user):
    active_episode = patient.get_active_episode()
    subs = [
        i for i in subrecords.subrecords() if not i == lmodels.LabTest
    ]
    subs.append(omodels.Tagging)

    serialised_episodes = serialised(
        patient.episode_set.all(), user, subs
    )
    episode_id_to_episode = {i["id"]: i for i in serialised_episodes}
    d = {
        'id': patient.id,
        'episodes': episode_id_to_episode,
        'active_episode_id': active_episode.id if active_episode else None,
    }

    for model in subrecords.patient_subrecords():
        if model == lmodels.LabTest:
            continue
        subs = model.objects.filter(patient_id=patient.id)
        d[model.get_api_name()] = [
            subrecord.to_dict(user) for subrecord in subs
        ]
    return d


class PatientViewSet(viewsets.ViewSet):
    base_name = 'patient'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(omodels.Patient.objects.all(), pk=pk)
        omodels.PatientRecordAccess.objects.create(
            patient=patient, user=request.user
        )
        return json_response(patient_to_dict(patient, request.user))
