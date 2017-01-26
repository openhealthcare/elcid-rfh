import json

from rest_framework import viewsets
from rest_framework.response import Response
from elcid import gloss_api
from opal.core.api import (
    OPALRouter, patient_from_pk, LoginRequiredViewset,
)
from opal.core.api import router as opal_api_router
from opal.core.views import _build_json_response
from opal.core.api import PatientViewSet
from opal import models


class GlossEndpointApi(viewsets.ViewSet):
    base_name = 'glossapi'

    def create(self, request):
        request_data = json.loads(request.data)
        gloss_api.bulk_create_from_gloss_response(request_data)
        return Response("ok")

def gloss_api_query_monkey_patch(fn):
    """
    Decorator that passes an episode or returns a 404 from pk kwarg.
    """
    def query_api_first(self, request, pk=None):
        patient = models.Patient.objects.get(pk=pk)
        hospital_number = patient.demographics_set.get().hospital_number
        gloss_api.patient_query(hospital_number)
        return fn(self, request, pk=pk)
    return query_api_first


PatientViewSet.retrieve = gloss_api_query_monkey_patch(PatientViewSet.retrieve)


gloss_router = OPALRouter()
gloss_router.register('glossapi', GlossEndpointApi)
