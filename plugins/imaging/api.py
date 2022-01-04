"""
API for imaging
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response


class ImagingViewSet(LoginRequiredViewset):
    basename = 'upstream_imaging'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        imaging = patient.imaging.all().order_by('-date_reported')
        result_code = request.GET.get("result_code")
        if result_code:
            imaging = imaging.filter(result_code=result_code)
        return json_response([r.to_dict() for r in imaging])
