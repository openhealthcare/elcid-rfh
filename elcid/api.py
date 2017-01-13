import json

from rest_framework import viewsets
from rest_framework.response import Response
from elcid import gloss_api
from opal.core.api import (
    OPALRouter, patient_from_pk, LoginRequiredViewset,
)
from opal.core.api import router as opal_api_router
from opal.core.views import _build_json_response


class GlossEndpointApi(viewsets.ViewSet):
    base_name = 'glossapi'

    def create(self, request):
        request_data = json.loads(request.data)
        gloss_api.bulk_create_from_gloss_response(request_data)
        return Response("ok")


class RefreshPatientApi(LoginRequiredViewset):
    """ goes to gloss, updates the patient locally
        and sends a copy of that patient to the client
    """
    base_name = "refresh-patient"

    @patient_from_pk
    def retrieve(self, request, patient):
        hospital_number = patient.demographics_set.get().hospital_number
        gloss_api.patient_query(hospital_number)
        return _build_json_response(patient.to_dict(request.user))


gloss_router = OPALRouter()
gloss_router.register('glossapi', GlossEndpointApi)

opal_api_router.register('refresh_patient', RefreshPatientApi)
