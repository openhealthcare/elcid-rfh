import json
from django.conf import settings

from rest_framework import viewsets
from rest_framework.response import Response
from elcid import gloss_api
from opal.core.api import OPALRouter
from opal.core.api import PatientViewSet
from opal.core.views import json_response
from opal import models
from elcid import models as emodels


class GlossEndpointApi(viewsets.ViewSet):
    base_name = 'glossapi'

    def create(self, request):
        request_data = json.loads(request.data)
        gloss_api.bulk_create_from_gloss_response(request_data)
        return Response("ok")


class ReleventLabTestApi(viewsets.ViewSet):
    base_name = 'relevent_lab_test_api'

    def list(self, request):
        test_data = emodels.HL7Result.get_relevant_tests()
        relevant_tests = [
            "C REACTIVE PROTEIN",
#            "FULL BLOOD COUNT",
            # "UREA AND ELECTROLYTES",
#            "LIVER PROFILE",
#            "GENTAMICIN LEVEL",
            # "CLOTTING SCREEN"
        ]
        for relevant_test in relevant_tests:
            grouped = [t for t in test_data if t.extras['profile_description'] == relevant_test]
            timeseries = []
            for group in grouped:
                for observation in group.extras["observations"]:
                    if observation["test_name"] == "C Reactive Protein":
                        units = observation["units"]
                        reference_range = observation["reference_range"]
                        timeseries.append((observation["observation_value"], group.date_ordered, ))
            for_rendering = {
                'name': "C Reactive Protein",
                'values': timeseries,
                'unit': units,
                'range': reference_range
            }

        return json_response([for_rendering])


def gloss_api_query_monkey_patch(fn):
    """
    Decorator that passes an episode or returns a 404 from pk kwarg.
    """
    def query_api_first(self, request, pk=None):
        if settings.GLOSS_ENABLED:
            patient = models.Patient.objects.get(pk=pk)
            hospital_number = patient.demographics_set.get().hospital_number
            gloss_api.patient_query(hospital_number)
        return fn(self, request, pk=pk)
    return query_api_first

PatientViewSet.retrieve = gloss_api_query_monkey_patch(PatientViewSet.retrieve)


gloss_router = OPALRouter()
gloss_router.register('glossapi', GlossEndpointApi)
gloss_router.register('relevent_lab_test_api', ReleventLabTestApi)
