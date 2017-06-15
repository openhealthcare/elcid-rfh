import json
import datetime
from operator import itemgetter
from collections import defaultdict
from django.conf import settings
from django.utils.text import slugify
from django.http import Http404

from rest_framework import viewsets
from rest_framework.response import Response
from elcid import gloss_api
from opal.core.api import OPALRouter
from opal.core.api import PatientViewSet, patient_from_pk, LoginRequiredViewset
from opal.core.views import json_response
from opal import models
from elcid import models as emodels
from lab import models as lmodels


_LAB_TEST_TAGS = {
    "BIOCHEMISTRY": [
        "BONE PROFILE",
        "UREA AND ELECTROLYTES",
        "LIVER PROFILE",
        "IMMUNOGLOBULINS",
        "C REACTIVE PROTEIN",
        "RENAL"

    ],
    "HAEMATOLOGY": [
        "FULL BLOOD COUNT", "HAEMATINICS", "HBA1C"
    ],
    "ENDOCRINOLOGY": [
        "CORTISOL AT 9AM", "THYROID FUNCTION TESTS"
    ],
    "URINE": [
        "OSMALITY", "PROTEIN ELECTROPHORESIS"
    ],
}

LAB_TEST_TAGS = defaultdict(list)

for tag, profile_descriptions in _LAB_TEST_TAGS.items():
    for profile_description in profile_descriptions:
        LAB_TEST_TAGS[profile_description].append(tag)


class GlossEndpointApi(viewsets.ViewSet):
    base_name = 'glossapi'

    def create(self, request):
        request_data = json.loads(request.data)
        gloss_api.bulk_create_from_gloss_response(request_data)
        return Response("ok")


class ObservationCollection(object):
    def clean_ref_range(self, obv):
        ref_range = obv["reference_range"]
        return ref_range.replace("]", "").replace("[", "")

    def get_reference_range(self, observation):
        observation["reference_range"] = observation["reference_range"]
        ref_range = self.clean_ref_range(observation)
        if not len(ref_range.replace("-", "").strip()):
            return None
        range_min_max = observation["reference_range"].split("-")
        if len(range_min_max) > 2:
            return None
        return {"min": range_min_max[0], "max": range_min_max[1]}

    def to_date_str(self, some_date):
        return some_date.strftime(
            settings.DATE_INPUT_FORMATS[0]
        )

    def __init__(self, observations):
        obv = observations[0]
        self.observations = observations
        self.test_name = obv["test_name"]
        self.units = obv["units"]
        self.reference_range = self.get_reference_range(obv)

    def to_dict(self):
        return {
            "observations": self.observations,
            "test_name": self.test_name,
            "units": self.units,
            "reference_range": self.reference_range
        }


class LabTestObservationDetail(LoginRequiredViewset):
    base_name = "lab_test_observation_detail"
    lookup_field = "slug"

    def retrieve(self, request, slug=None):
        found_observations = []
        for lab_test in lmodels.LabTest.objects.all():
            existing_observations = lab_test.extras.get("observations", [])

            for existing_observation in existing_observations:
                sluged_test_name = slugify(
                    existing_observation.get("test_name", None)
                )
                if sluged_test_name == slug:
                    existing_observation["date_ordered"] = lab_test.date_ordered
                    found_observations.append(existing_observation)

        if not found_observations:
            raise Http404
        collection = ObservationCollection(found_observations)
        return json_response(collection.to_dict())


class LabTestResultsView(LoginRequiredViewset):
    """ The Api view of the the results view in the patient detail
        We want to show everything grouped by test, then observation, then
        date.
    """
    base_name = 'lab_test_results_view'

    def generate_time_series(self, observations):
        timeseries = []
        for observation in observations:
            obs_result = observation["observation_value"].split("~")[0]
            try:
                # we can fail if the result is not numeric
                timeseries.append(
                    float(obs_result),
                )
            except ValueError:
                timeseries.append((
                    None,
                ))
        if len([t for t in timeseries if not t == 'values' and t]) > 3:
            return timeseries
        else:
            return []

    def to_date_str(self, some_date):
        return some_date.strftime(
            settings.DATE_INPUT_FORMATS[0]
        )

    @patient_from_pk
    def retrieve(self, request, patient):
        # so what I want to return is all observations to lab test desplay
        # name with the lab test properties on the observation

        three_months_ago = datetime.date.today() - datetime.timedelta(3*30)
        lab_tests = lmodels.LabTest.objects.filter(patient=patient)
        # lab_tests = lab_tests.filter(date_ordered__gte=three_months_ago)
        by_test = defaultdict(list)

        # lab tests are sorted by lab test type
        # this is either the lab test type if its a lab test we've
        # defined or its what is in the profile description
        # if its an HL7 jobby
        for lab_test in lab_tests:
            as_dict = lab_test.to_dict(None)
            observations = as_dict.get("observations", [])
            lab_test_type = as_dict["extras"].get(
                "profile_description", lab_test.lab_test_type
            )

            for observation in observations:
                observation["reference_range"] = observation["reference_range"].replace("]", "").replace("[", "")
                if not len(observation["reference_range"].replace("-", "").strip()):
                    observation["reference_range"] = None
                    continue
                range_min_max = observation["reference_range"].split("-")
                if not range_min_max[0].strip():
                    observation["reference_range"] = None
                else:
                    if not len(range_min_max) == 2:
                        observation["reference_range"] = None
                        # raise ValueError("unable to properly judge the range")
                    else:
                        observation["reference_range"] = dict(
                            min=float(range_min_max[0].strip()),
                            max=float(range_min_max[1].strip())
                        )

                observation["date_ordered"] = lab_test.date_ordered
                observation["api_name"] = slugify(observation["test_name"])
                by_test[lab_test_type].append(observation)

        serialised_tests = []

        # within the lab test observations should be sorted by test name
        # and within the if we have a date range we want to be exposing
        # them as part of a time series, ie adding in blanks if they
        # aren't populated
        for lab_test_type, observations in by_test.items():
            observations = sorted(observations, key=lambda x: x["date_ordered"])
            observations.reverse()
            observations = sorted(observations, key=lambda x: x["test_name"])

            # observation_time_series = defaultdict(list)
            by_observations = defaultdict(list)
            observation_metadata = {}

            observation_date_range = {
                observation["date_ordered"] for observation in observations
            }
            observation_date_range = sorted(list(observation_date_range))
            observation_date_range.reverse()

            for observation in observations:
                test_name = observation["test_name"]

                if test_name not in by_observations:
                    obs_for_test_name = {
                        self.to_date_str(i["date_ordered"]): i for i in observations if i["test_name"] == test_name
                    }
                    by_observations[test_name] = obs_for_test_name

                if test_name not in observation_metadata:
                    observation_metadata[test_name] = dict(
                        units=observation["units"],
                        reference_range=observation["reference_range"]
                    )

            # # construct time series from the labtest/observation/daterange key values
            # for observation_name, observations_by_date in by_observations.items():
            #     for observation_date in observation_date_range:
            #         obvs_dict = observations_by_date.get(self.to_date_str(observation_date), None)
            #         obvs_value = None
            #         if obvs_dict:
            #             obvs_value = obvs_dict["observation_value"]
            #         observation_time_series[observation_name].append(
            #             obvs_value
            #         )

            serialised_lab_teset = dict(
                observation_metadata=observation_metadata,
                lab_test_type=lab_test_type,
                observations=observations,
                observation_date_range=observation_date_range,
                # observation_time_series=observation_time_series,
                by_observations=by_observations,
                observation_names=sorted(by_observations.keys()),
                tags = LAB_TEST_TAGS.get(lab_test_type, [])
            )
            serialised_tests.append(serialised_lab_teset)

            serialised_tests = sorted(serialised_tests, key=itemgetter("lab_test_type"))

            all_tags = _LAB_TEST_TAGS.keys()

        return json_response(
            dict(
                tags=all_tags,
                tests=serialised_tests
            )
        )


class ReleventLabTestApi(LoginRequiredViewset):
    """ The API View used in the card list. Returns the last 3 months (approixmately)
        of the tests we care about the most.
    """
    base_name = 'relevent_lab_test_api'

    PREFERRED_ORDER = [
        "WBC",
        "Lymphocytes",
        "Neutrophils",
        "INR",
        "C Reactive Protein",
        "ALT",
        "AST",
        "Alkaline Phosphatase"
    ]

    def sort_observations(self, obv):
        if obv["name"] in self.PREFERRED_ORDER:
            return self.PREFERRED_ORDER.index(obv["name"])
        else:
            return len(self.PREFERRED_ORDER)

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
                                    obs_result,
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

        obs_values = sorted(obs_values, key=self.sort_observations)
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
gloss_router.register('lab_test_observation_detail', LabTestObservationDetail)
