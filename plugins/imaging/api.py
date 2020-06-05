"""
API for imaging
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response


class ImagingViewSet(LoginRequiredViewset):
    base_name = 'imaging'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        imaging = patient.imaging.all().order_by('-date_reported')
        return json_response([r.to_dict() for r in imaging])
