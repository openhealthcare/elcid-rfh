from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from opal.core.views import json_response
from opal import models as omodels
from opal.core import subrecords
from lab import models as lmodels
from elcid.episode_serialization import serialize
from intrahospital_api import lab_tests as lab_test_service


def patient_to_dict(patient, user):
    active_episode = patient.get_active_episode()
    subs = [
        i for i in subrecords.subrecords() if not i == lmodels.LabTest
    ]
    subs.append(omodels.Tagging)

    serialised_episodes = serialize(
        patient.episode_set.all(), user, subs
    )
    d = {
        'id': patient.id,
        'active_episode_id': active_episode.id if active_episode else None
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

    return d


class UpstreamDataViewset(viewsets.ViewSet):
    base_name = 'upstream'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(
            omodels.Patient.objects.all(), pk=pk
        )
        hospital_number = patient.demographics_set.first().hospital_number
        return json_response(lab_test_service.lab_tests_for_hospital_number(hospital_number))


class PatientViewSet(viewsets.ViewSet):
    base_name = 'patient'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(omodels.Patient.objects.all(), pk=pk)
        omodels.PatientRecordAccess.objects.create(
            patient=patient, user=request.user
        )
        return json_response(patient_to_dict(patient, request.user))
