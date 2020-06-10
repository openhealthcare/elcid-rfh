"""
API for discharge summaries
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response


class DischargeSummaryViewSet(LoginRequiredViewset):
    base_name = 'dischargesummaries'

    def retrieve(self, request, pk):
        patient    = get_object_or_404(Patient.objects.all(), pk=pk)
        data = {}
        return json_response([{}])
