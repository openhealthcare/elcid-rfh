"""
API for RNOH SBAR data
"""
from opal.core.api import LoginRequiredViewset, patient_from_pk
from opal.core.views import json_response


class SBARViewSet(LoginRequiredViewset):
    basename = 'sbar'

    @patient_from_pk
    def retrieve(self, request, patient):
        sbars = patient.rnoh_sbar.all()
        return json_response([a.to_dict() for a in sbars])
