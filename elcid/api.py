import json
import datetime
from collections import defaultdict
from django.conf import settings

from rest_framework import viewsets
from rest_framework.response import Response
from elcid import gloss_api
from opal.core.api import OPALRouter
from opal.core.api import PatientViewSet, patient_from_pk, LoginRequiredViewset
from opal.core.views import json_response
from opal import models
from elcid import models as emodels
from lab import models as lmodels


class GlossEndpointApi(viewsets.ViewSet):
    base_name = 'glossapi'

    def create(self, request):
        request_data = json.loads(request.data)
        gloss_api.bulk_create_from_gloss_response(request_data)
        return Response("ok")


class LabTestResultsView(LoginRequiredViewset):
    """ The Api view of the the results view in the patient detail
        We want to show everything grouped by test, then observation, then
        date.
    """
    base_name = 'lab_test_results_view'

    @patient_from_pk
    def retrieve(self, request, patient):
        # so what I want to return is all observations to lab test desplay
        # name with the lab test properties on the observation

        three_months_ago = datetime.date.today() - datetime.timedelta(3*30)
        lab_tests = lmodels.LabTest.objects.filter(patient=patient)
        lab_tests = lab_tests.filter(date_ordered__gte=three_months_ago)
        result = defaultdict(list)

        for lab_test in lab_tests:
            as_dict = lab_test.to_dict(None)
            observations = as_dict.get("observations", [])
            lab_test_type = as_dict["extras"].get(
                "profile_description", lab_test.lab_test_type
            )

            for observation in observations:
                observation["date_ordered"] = lab_test.date_ordered
                result[lab_test_type].append(observation)
        return json_response(result)


class ReleventLabTestApi(LoginRequiredViewset):
    """ The API View used in the card list. Returns the last 3 months (approixmately)
        of the tests we care about the most.
    """
    base_name = 'relevent_lab_test_api'

    @patient_from_pk
    def retrieve(self, request, patient):
        test_data = emodels.HL7Result.get_relevant_tests(patient)
        relevant_tests = {
            "C REACTIVE PROTEIN": ["C Reactive Protein"],
            "FULL BLOOD COUNT": ["WBC", "Lymphocytes", "Neutrophils"],
            "LIVER PROFILE": ["ALT", "AST", "Alkaline Phosphatase"],
            "CLOTTING SCREEN": ["INR"]
        }

        obs_values = []
        all_dates = set()
        units = None
        reference_range = None
        for relevant_test, relevant_observations in relevant_tests.items():
            for relevant_observation in relevant_observations:
                grouped = [t for t in test_data if t.extras['profile_description'] == relevant_test]
                timeseries = []
                for group in grouped:
                    for observation in group.extras["observations"]:
                        if observation["test_name"] == relevant_observation:
                            units = observation["units"]
                            reference_range = observation["reference_range"]
                            obs_result = observation["observation_value"].split("~")[0]

                            try:
                                float(obs_result)
                                timeseries.append((
                                    observation["observation_value"].split("~")[0],
                                    group.date_ordered,
                                ))
                                all_dates.add(group.date_ordered)
                            except ValueError:
                                timeseries.append((
                                    None,
                                    group.date_ordered,
                                ))

                # sort by date reversed
                timeseries = sorted(timeseries, key=lambda x: x[1])
                timeseries.reverse()

                obs_values.append({
                    'name': relevant_observation.strip(),
                    'values': timeseries,
                    'unit': units,
                    'range': reference_range
                })

        # so we want a table that shows the latest three dates
        # so we get the latest three dates that these tests have
        # and then we create an dictionary of of the latest 3 results {date: value}
        # not all dates will have an element, we'll leave those blank
        latest_results = sorted(list(all_dates))[:3]
        latest_results.reverse()

        for obs_value in obs_values:
            obs_value["latest_results"] = {}
            for series_element in obs_value["values"]:
                if series_element[1] in latest_results:
                    date_var = series_element[1].strftime(
                        settings.DATE_INPUT_FORMATS[0]
                    )
                    print series_element[0]
                    obs_value["latest_results"][date_var] = series_element[0]

        result = dict(
            obs_values=obs_values,
            latest_results=latest_results
        )
        return json_response(result)


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
gloss_router.register('lab_test_results_view', LabTestResultsView)
