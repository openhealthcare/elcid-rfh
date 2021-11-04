"""
API for admission data
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response

EXCLUDE_ADMISSIONS = [
    # We previously excluded these based on eyeballing data for admissions before
    # we had learned to update them in place adequately.
    # These message types are under active review, and the existing list definitely
    # excluded current active admissions e.g. patients in the building where
    # we had valid location data for them.

    # 'A14', # Pending admit
    # 'A35', # Merge account num
    # 'S12', # New Appt
    # 'S13', # Reschedule Appt
    # 'S14', # Modify Appt
    # 'S15'  # Cancel Appt
]

class AdmissionViewSet(LoginRequiredViewset):
    basename = 'admissions'

    def retrieve(self, request, pk):
        patient    = get_object_or_404(Patient.objects.all(), pk=pk)
        admissions = patient.encounters.exclude(
            msh_9_msg_type__in=EXCLUDE_ADMISSIONS
        ).order_by('last_updated')
        return json_response([a.to_dict() for a in admissions])
