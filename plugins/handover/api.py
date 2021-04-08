"""
API definition for handover plugin
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response


class AMTHandoverViewSet(LoginRequiredViewset):
    base_name = 'amthandovers'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        data = [
            h.to_dict() for h in patient.amt_handover.all().order_by('-sqlserver_insert_datetime')
        ]
        return json_response(data)


class NursingHandoverViewSet(LoginRequiredViewset):
    base_name = 'nursinghandovers'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        data = [
            h.to_dict() for h in patient.nursing_handover.all().order_by('-sqlserver_insert_datetime')
        ]
        return json_response(data)
