from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from opal.core.views import json_response
from opal import models as omodels
from opal.core import subrecords
from lab import models as lmodels
from elcid import models as emodels
from elcid.episode_serialization import serialize
from intrahospital_api import get_api


def patient_to_dict(patient, user):
    subs = [
        i for i in subrecords.subrecords() if not i == lmodels.LabTest
    ]
    subs.append(omodels.Tagging)

    episodes = patient.episode_set.all()

    serialised_episodes = serialize(
        episodes, user, subs
    )
    d = {
        'id': patient.id,
    }
    for model in subrecords.patient_subrecords():
        if model == lmodels.LabTest:
            subs = model.objects.filter(patient_id=patient.id).filter(
                external_system=None
            )
            d[model.get_api_name()] = [
                subrecord.to_dict(user) for subrecord in subs
            ]
        else:
            subs = model.objects.filter(patient_id=patient.id)
            d[model.get_api_name()] = [
                subrecord.to_dict(user) for subrecord in subs
            ]

        for episode_dict in serialised_episodes:
            if model.get_api_name() in d:
                if d[model.get_api_name()]:
                    episode_dict[model.get_api_name()] = d[
                        model.get_api_name()
                    ]

    episode_id_to_episode = {i["id"]: i for i in serialised_episodes}
    d["episodes"] = episode_id_to_episode

    antifungal_episodes = emodels.ChronicAntifungal.antifungal_episodes()
    d["is_antifungal"] = antifungal_episodes.filter(
        id__in=episodes.values_list('id', flat=True)
    ).exists()

    return d


class UpstreamDataViewset(viewsets.ViewSet):
    base_name = 'upstream'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(
            omodels.Patient.objects.all(), pk=pk
        )
        api = get_api()
        hospital_number = patient.demographics_set.first().hospital_number
        return json_response(api.results_for_hospital_number(hospital_number))


class PatientViewSet(viewsets.ViewSet):
    base_name = 'patient'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(omodels.Patient.objects.all(), pk=pk)
        omodels.PatientRecordAccess.objects.create(
            patient=patient, user=request.user
        )
        return json_response(patient_to_dict(patient, request.user))
