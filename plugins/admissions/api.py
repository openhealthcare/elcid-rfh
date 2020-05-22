"""
API for admission data
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response

EXCLUDE_ADMISSIONS = [
    'A14', # Pending admit
    'A35', # Merge account num
    'S12', # New Appt
    'S13', # Reschedule Appt
    'S14', # Modify Appt
    'S15'  # Cancel Appt
]

class AdmissionViewSet(LoginRequiredViewset):
    base_name = 'admissions'

    def retrieve(self, request, pk):
        patient    = get_object_or_404(Patient.objects.all(), pk=pk)
        admissions = patient.encounters.exclude(
            msh_9_msg_type__in=EXCLUDE_ADMISSIONS
        ).order_by('-evn_2_movement_date')
        return json_response([a.to_dict() for a in admissions])
