"""
DRF API endpoints:

* Overriding the core Opal Patient API endoint
* Providing lab tests as a separate API call (due to volume/performance)
"""
from django.shortcuts import get_object_or_404
from lab import models as lmodels
from opal.core.views import json_response
from opal import models as omodels
from opal.core import subrecords
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

from elcid.episode_serialization import serialize
from intrahospital_api.services.lab_tests import service as lab_test_service


def patient_to_dict(patient, user):
    """
    Serialize a patient without LabTests (faster, there are lots.)

    This code copied from Opal core until we can override without needing to.
    """
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
    """
    A badly named class and API endpoint that retrieves lab test data
    """
    base_name = 'upstream'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        """
        GET endpoint for our API - 404 or serialized tests.
        """
        patient = get_object_or_404(
            omodels.Patient.objects.all(), pk=pk
        )
        hospital_number = patient.demographics_set.first().hospital_number
        return json_response(
            lab_test_service.lab_tests_for_hospital_number(hospital_number)
        )


class PatientViewSet(viewsets.ViewSet):
    """
    Overriding the Opal Core Patient API endpoint in order to exclude lab tests
    from serialization due to volume (performance).
    """
    base_name = 'patient'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        """
        GET endpoint for our API - seriliase with our custom serializer.
        """
        patient = get_object_or_404(omodels.Patient.objects.all(), pk=pk)
        omodels.PatientRecordAccess.objects.create(
            patient=patient, user=request.user
        )
        return json_response(patient_to_dict(patient, request.user))
