import datetime
import re
from django.conf import settings
from operator import itemgetter
from collections import defaultdict, OrderedDict
from django.utils.text import slugify
from django.http import HttpResponseBadRequest
from intrahospital_api import loader
from rest_framework import viewsets, status
from opal.core.api import OPALRouter
from opal.core.api import (
    patient_from_pk, LoginRequiredViewset, SubrecordViewSet
)
from opal.core.views import json_response
from opal.core import serialization
from elcid import models as emodels
from plugins.labtests import models as lab_test_models


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

_ALWAYS_SHOW_AS_TABULAR = [
    "UREA AND ELECTROLYTES",
    "LIVER PROFILE",
    "IMMUNOGLOBULINS",
    "C REACTIVE PROTEIN",
    "RENAL",
    "RENAL PROFILE",
    "BONE PROFILE",
    "FULL BLOOD COUNT",
    "HAEMATINICS",
    "HBA1C",
    "THYROID FUNCTION TESTS",
    "ARTERIAL BLOOD GASES",
    "B12 AND FOLATE SCREEN",
    "CLOTTING SCREEN",
    "BICARBONATE",
    "CARDIAC PROFILE",
    "CHLORIDE",
    "CHOLESTEROL/TRIGLYCERIDES",
    "AFP",
    "25-OH VITAMIN D",
    "AMMONIA",
    "FLUID CA-125",
    "CARDIAC TROPONIN T",
    "BODYFLUID CALCIUM",
    "BODYFLUID GLUCOSE",
    "BODYFLUID POTASSIUM",
    "PDF PROTEIN",
    "TACROLIMUS",
    "FULL BLOOD COUNT"
]

LAB_TEST_TAGS = defaultdict(list)


for tag, test_names in _LAB_TEST_TAGS.items():
    for test_name in test_names:
        LAB_TEST_TAGS[test_name].append(tag)


AEROBIC = "aerobic"
ANAEROBIC = "anaerobic"


class LabTestResultsView(LoginRequiredViewset):
    """ The Api view of the the results view in the patient detail
        We want to show everything grouped by test, then observation, then
        date.
    """
    base_name = 'lab_test_results_view'

    def get_observation_value(self, observation):
        obs_result = observation.value_numeric

        if obs_result:
            return obs_result

        return observation.observation_value

    def get_observations_by_lab_test(self, lab_tests):
        by_test = defaultdict(list)

        for lab_test in lab_tests:
            observations = lab_test.observation_set.all()
            lab_test_type = lab_test.test_name

            for observation in observations:
                if observation.observation_name.strip() == "Haem Lab Comment":
                    continue
                if observation.observation_name.strip() == "Sample Comment":
                    continue

                # if its all None's for a certain observation name lets skip it
                # ie if WBC is all None, lets not waste the users' screen space
                # sometimes they just have '-' so lets skip these too
                if self.is_empty_value(observation.observation_value):
                    continue

                by_test[lab_test_type].append(observation)

        return by_test

    def is_empty_value(self, observation_value):
        """ we don't care about empty strings or
            ' - ' or ' # '
        """
        if isinstance(observation_value, str):
            return not observation_value.strip().strip("-").strip("#").strip()
        else:
            return observation_value is None

    def get_non_comments_for_patient(self, patient):
        to_ignore = ['UNPROCESSED SAMPLE COMT', 'COMMENT', 'SAMPLE COMMENT']

        lab_tests = patient.lab_tests.all()
        lab_tests = lab_tests.exclude(
            test_name__in=to_ignore
        )
        return lab_tests.prefetch_related('observation_set')

    def get_observations_by_type_and_date_str(self, observations):
        """
        Returns a dict of observation name -> date -> observation
        We choose the most recent datetime for the date unless the most
        recent is 'Pending'
        """
        result = defaultdict(dict)
        observations = sorted(
            observations,
            key=lambda x: x.observation_datetime,
            reverse=True
        )
        for observation in observations:
            obs_dict = result[observation.observation_name]
            obs_date = serialization.serialize_date(
                observation.observation_datetime.date()
            )
            obs_value = self.get_observation_value(
                observation
            )
            if obs_date not in obs_dict:
                if observation.is_pending:
                    obs_dict[obs_date] = "Pending"
                else:
                    obs_dict[obs_date] = obs_value
            else:
                if obs_dict[obs_date] == "Pending":
                    obs_dict[obs_date] = obs_value

        return result

    def get_date_range(self, observations):
        observation_date_range = set()

        for observation in observations:
            observation_date_range.add(observation.observation_datetime.date())
        return sorted(list(observation_date_range))

    def is_long_form(self, lab_test_type, observations):
        """
        and whether the observations should be displayed in a table
        form or long form
        """
        if lab_test_type in _ALWAYS_SHOW_AS_TABULAR:
            return False

        for observation in observations:
            if not observation.value_numeric:
                if not observation.is_pending:
                    return True
        return False

    def get_observation_metadata(self, observations):
        observation_metadata = {}
        for observation in observations:
            obs_name = observation.observation_name
            observation_metadata[obs_name] = dict(
                units=observation.units,
                reference_range=observation.cleaned_reference_range,
                api_name=slugify(observation.observation_name)
            )
        return observation_metadata

    def sort_lab_tests_dicts(self, lab_test_dicts):
        """
        Ordered by most recent observations first please, this means
        the first date if its a long form observation or the last
        if its not. (as short form dates are shown ascending and long form descending)

        When there are multiple results for the same date, tests should be shown in
        alphabetical order.
        """
        serialised_tests = sorted(
            lab_test_dicts, key=itemgetter("lab_test_type")
        )

        def get_latest_date(obs_dict):
            if obs_dict["long_form"]:
                return obs_dict["observation_date_range"][0]
            else:
                return obs_dict["observation_date_range"][-1]

        # ordered by most recent observations first please, bu maintaining
        # the alphabetically order of the lab tests
        serialised_tests = sorted(
            serialised_tests, key=get_latest_date, reverse=True
        )
        return serialised_tests

    @patient_from_pk
    def retrieve(self, request, patient):

        # so what I want to return is all observations to lab test desplay
        # name with the lab test properties on the observation
        lab_tests = self.get_non_comments_for_patient(patient)
        by_test = self.get_observations_by_lab_test(lab_tests)
        serialised_tests = []

        # within the lab test observations should be sorted by test name
        # and within the if we have a date range we want to be exposing
        # them as part of a time series, ie adding in blanks if they
        # aren't populated
        for lab_test_type, observations in by_test.items():
            by_observations = self.get_observations_by_type_and_date_str(
                observations
            )
            observation_date_range = self.get_date_range(observations)
            observation_metadata = self.get_observation_metadata(observations)
            long_form = self.is_long_form(lab_test_type, observations)

            if long_form:
                # when we are showing in long form the user sees tests as a
                # list so show the most recent test first
                observation_date_range.reverse()
            else:
                # if we're not in long form ie we're displaying results
                # in a tabular timeline, we only want to display
                # the 7 most recent results.
                observation_date_range = observation_date_range[-7:]

            serialised_lab_test = dict(
                long_form=long_form,
                api_name=slugify(lab_test_type),
                observation_metadata=observation_metadata,
                lab_test_type=lab_test_type,
                observation_date_range=observation_date_range,
                # observation_time_series=observation_time_series,
                by_observations=by_observations,
                observation_names=sorted(by_observations.keys()),
                tags=LAB_TEST_TAGS.get(lab_test_type, [])
            )
            serialised_tests.append(serialised_lab_test)

        serialised_tests = self.sort_lab_tests_dicts(serialised_tests)

        all_tags = list(_LAB_TEST_TAGS.keys())

        return json_response(
            dict(
                tags=all_tags,
                tests=serialised_tests
            )
        )


class InfectionServiceTestSummaryApi(LoginRequiredViewset):
    base_name = 'infection_service_summary_api'
    RELEVANT_TESTS = OrderedDict((
        ("FULL BLOOD COUNT", ["WBC", "Lymphocytes", "Neutrophils"],),
        ("CLOTTING SCREEN", ["INR"],),
        ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
        ("LIVER PROFILE", ["ALT", "AST", "Alkaline Phosphatase"]),
    ),)

    NUM_RESULTS = 5

    def get_recent_dates_to_observations(self, qs):
        """
        We are looking for the last 5 dates
        where we have any observation that
        can be cast to a number.

        If a patient has multiple observations
        on the same date take the most recent
        that can be cast into a number
        """
        date_to_observation = {}
        # this should never be the case, but
        # we don't create the data so cater for it
        qs = qs.exclude(observation_datetime=None)
        for i in qs.order_by("-observation_datetime"):
            if i.value_numeric is not None:
                dt = i.observation_datetime
                obs_date = dt.date()
                if obs_date in date_to_observation:
                    if date_to_observation[obs_date].observation_datetime < dt:
                        date_to_observation[obs_date] = i
                else:
                    date_to_observation[obs_date] = i
            if len(date_to_observation.keys()) == self.NUM_RESULTS:
                break

        return date_to_observation

    def get_obs_queryset(self, patient, lab_test_name, observation_name):
        return lab_test_models.Observation.objects.filter(
            test__patient=patient
        ).filter(
            test__test_name=lab_test_name
        ).filter(
            observation_name=observation_name
        )

    def serialize_observations(self, observations):
        latest_results = {
            serialization.serialize_date(i.observation_datetime.date()): i.value_numeric
            for i in observations
        }
        return dict(
            name=observations[0].observation_name,
            units=observations[0].units,
            reference_range=observations[0].cleaned_reference_range,
            latest_results=latest_results
        )

    def serialise_lab_tests(self, patient):
        obs = []
        date_set = set()

        for test_name, observation_names in self.RELEVANT_TESTS.items():
            for obs_name in observation_names:
                qs = self.get_obs_queryset(patient, test_name, obs_name)
                if qs:
                    date_to_obs = self.get_recent_dates_to_observations(qs)
                    if date_to_obs:
                        date_set.update(date_to_obs.keys())
                        obs.append(list(date_to_obs.values()))

        all_dates = list(date_set)
        all_dates.sort()
        recent_dates = all_dates[-self.NUM_RESULTS:]

        # flush out the recent dates with nulls if
        # the patient does not have a lot of results
        while len(recent_dates) < self.NUM_RESULTS:
            recent_dates.append(None)
        obs_values = []

        for obs_set in obs:
            obs_values.append(self.serialize_observations(obs_set))
        return dict(
            obs_values=obs_values,
            recent_dates=recent_dates
        )

    @patient_from_pk
    def retrieve(self, request, patient):
        result = self.serialise_lab_tests(patient)
        return json_response(result)


class UpstreamBloodCultureApi(viewsets.ViewSet):
    """
        for every upstream blood culture, return them grouped by

        datetimes_ordered as a date,
        lab_number
        observation name
    """
    base_name = "upstream_blood_culture_results"

    def no_growth_observations(self, observations):
        """
            We are looking for observations that looks like the below.
            Its not necessarily 5 days, sometimes its e.g. 48 hours.
            Otherwise they always look like the below.

            Aerobic bottle culture: No growth after 5 days of incubation
            Anaerobic bottle culture: No growth after 5 days of incubation

            The are always of the type [Anaerobic/Aerobic] bottle culture
        """
        obs_names = ["Aerobic bottle culture", "Anaerobic bottle culture"]

        bottles = [
            o for o in observations if o["observation_name"] in obs_names
        ]

        return len(bottles) == 2

    @patient_from_pk
    def retrieve(self, request, patient):
        """
            returns any observations with Aerobic or Anaerobic in their name
        """
        lab_tests = patient.labtest_set.filter(
            lab_test_type=emodels.UpstreamBloodCulture.get_display_name()
        ).order_by("external_identifier").order_by("-datetime_ordered")
        lab_tests = [i.dict_for_view(request.user) for i in lab_tests]
        for lab_test in lab_tests:
            observations = []
            lab_test["no_growth"] = self.no_growth_observations(
                lab_test["observations"]
            )

            for observation in lab_test["observations"]:
                ob_name = observation["observation_name"].lower()

                if "aerobic" in ob_name:
                    observations.append(observation)

            lab_test["observations"] = sorted(
                observations, key=lambda x: x["observation_name"]
            )
            if lab_test["extras"]["clinical_info"]:
                lab_test["extras"]["clinical_info"] = "{}{}".format(
                    lab_test["extras"]["clinical_info"][0].upper(),
                    lab_test["extras"]["clinical_info"][1:]
                )

        return json_response(dict(
            lab_tests=lab_tests
        ))


class DemographicsSearch(LoginRequiredViewset):
    base_name = 'demographics_search'
    PATIENT_FOUND_IN_ELCID = "patient_found_in_elcid"
    PATIENT_FOUND_UPSTREAM = "patient_found_upstream"
    PATIENT_NOT_FOUND = "patient_not_found"

    def list(self, request, *args, **kwargs):
        hospital_number = request.query_params.get("hospital_number")
        if not hospital_number:
            return HttpResponseBadRequest("Please pass in a hospital number")
        demographics = emodels.Demographics.objects.filter(
            hospital_number=hospital_number
        ).last()

        # the patient is in elcid
        if demographics:
            return json_response(dict(
                patient=demographics.patient.to_dict(request.user),
                status=self.PATIENT_FOUND_IN_ELCID
            ))
        else:
            if settings.USE_UPSTREAM_DEMOGRAPHICS:
                demographics = loader.load_demographics(hospital_number)

                if demographics:
                    return json_response(dict(
                        patient=dict(demographics=[demographics]),
                        status=self.PATIENT_FOUND_UPSTREAM
                    ))
        return json_response(dict(status=self.PATIENT_NOT_FOUND))


class BloodCultureIsolateApi(SubrecordViewSet):
    model = emodels.BloodCultureIsolate
    base_name = emodels.BloodCultureIsolate.get_api_name()

    def create(self, request):
        bc = self.model()
        bc.update_from_dict(request.data, request.user)
        return json_response(
            bc.to_dict(request.user),
            status_code=status.HTTP_201_CREATED
        )


elcid_router = OPALRouter()
elcid_router.register(
    UpstreamBloodCultureApi.base_name, UpstreamBloodCultureApi
)
elcid_router.register(DemographicsSearch.base_name, DemographicsSearch)
elcid_router.register(BloodCultureIsolateApi.base_name, BloodCultureIsolateApi)

lab_test_router = OPALRouter()
lab_test_router.register(
    'infection_service_summary_api', InfectionServiceTestSummaryApi
)
lab_test_router.register('lab_test_results_view', LabTestResultsView)
