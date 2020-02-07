"""
API endpoints for the elCID application
"""
import datetime
import re
from collections import defaultdict, OrderedDict
from operator import itemgetter

from django.conf import settings
from django.utils.text import slugify
from django.http import HttpResponseBadRequest
from rest_framework import viewsets, status
from opal.core.api import OPALRouter
from opal.core.api import (
    patient_from_pk, LoginRequiredViewset, SubrecordViewSet
)
from opal.core.views import json_response
from opal.core import serialization

from intrahospital_api import loader
from elcid import models as emodels
from plugins.labtests import models as lab_test_models


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


AEROBIC   = "aerobic"
ANAEROBIC = "anaerobic"


class LabTestResultsView(LoginRequiredViewset):
    """
    The API endpoint that returns data for the test results view on the
    patient detail page.
    """
    base_name = 'lab_test_results_view'

    def get_non_comments_for_patient(self, patient):
        """
        Returns all non comments for a patient, ensuring they are
        ordered by date and prefetching observations.
        """
        to_ignore = ['UNPROCESSED SAMPLE COMT', 'COMMENT', 'SAMPLE COMMENT']

        lab_tests = patient.lab_tests.all().order_by('-datetime_ordered')
        lab_tests = lab_tests.exclude(
            test_name__in=to_ignore
        )
        return lab_tests.prefetch_related('observation_set')

    def group_tests(self, lab_tests):
        """
        Return dictionary that groups a queryset of lab tests by test name.
        """
        by_test = defaultdict(list)

        for lab_test in lab_tests:
            by_test[lab_test.test_name].append(lab_test)
        return by_test

    def is_long_form(self, test_type, instances):
        """
        Predicate function that indicates whether results should
        be displayed in a table form or long form
        """
        if test_type in _ALWAYS_SHOW_AS_TABULAR:
            return False

        for instance in instances:
            for observation in instance.observation_set.all():
                if not observation.value_numeric:
                    if not observation.is_pending:
                        return True
        return False

    def is_empty_value(self, observation_value):
        """
        Predocate function that indicates whether there is a meaningful value
        in this string.

        For these purposes don't care about empty strings, ' - ', or ' # '
        """
        if isinstance(observation_value, str):
            return not observation_value.strip().strip("-").strip("#").strip()
        else:
            return observation_value is None

    def display_class_for_numeric_observation(self, observation):
        """
        Returns too-high too-low or '' for a numeric observation
        """
        display_class = ''
        numeric       = observation.value_numeric
        refrange      = observation.cleaned_reference_range

        if refrange is None:
            return display_class

        if numeric < refrange['min']:
            display_class = 'too-low'

        if numeric > refrange['max']:
            display_class = 'too-high'

        return display_class

    def serialise_tabular_instances(self, instances):
        """
        Serialise all instances of a tabular test type (e.g. Full Blood Count)
        """
        test_datetimes     = set()
        observation_names  = set()
        observation_ranges = {}
        lab_numbers        = {}
        data               = defaultdict(lambda: defaultdict(lambda: None))

        for instance in instances:
            test_datetimes.add(instance.datetime_ordered)
            lab_numbers[serialization.serialize_datetime(instance.datetime_ordered)] = instance.lab_number

            for observation in instance.observation_set.all():
                if not self.is_empty_value(observation.observation_value):

                    if observation.observation_name.rstrip('.') not in observation_ranges:
                        if observation.reference_range != " -":
                            observation_ranges[observation.observation_name.rstrip('.')] = observation.reference_range

                    observation_names.add(observation.observation_name.rstrip('.'))
                    data[observation.observation_name.rstrip('.')][serialization.serialize_datetime(instance.datetime_ordered)] = {
                        'value'        : observation.observation_value,
                        'range'        : observation.reference_range,
                        'display_class': self.display_class_for_numeric_observation(observation)
                    }


        date_series = list(sorted(test_datetimes))
        date_series = [serialization.serialize_datetime(d) for d in date_series]

        return {
            'test_datetimes'    : date_series[-8:],
            'observation_names' : list(sorted(observation_names)),
            'lab_numbers'       : lab_numbers,
            'observation_ranges': observation_ranges,
            'observation_series': data
        }

    def serialise_long_form_instance(self, instance):
        """
        Serialise a single long form test instance.
        """
        serialised_observations = []
        for o in instance.observation_set.all():
            if not self.is_empty_value(o.observation_value):
                serialised_observations.append(
                    {
                        'name' : o.observation_name.rstrip('.'),
                        'value': o.observation_value
                    }
                )

        return {
            'lab_number'  : instance.lab_number,
            'date'        : instance.datetime_ordered,
            'observations': serialised_observations

        }

    @patient_from_pk
    def retrieve(self, request, patient):
        """
        Main entrypoint for test results via the API.
        """
        lab_tests  = self.get_non_comments_for_patient(patient)
        test_dates = {}

        for test in lab_tests:
            if test.test_name in test_dates:
                if test_dates[test.test_name] > test.datetime_ordered:
                    continue
            test_dates[test.test_name] = test.datetime_ordered

        test_order = [
            d[0] for d in
            sorted(test_dates.items(),
                   key=lambda x: -x[1].timestamp())
        ]

        by_test          = self.group_tests(lab_tests)
        serialised_tests = {}
        test_dates       = {}

        for test_type, instances in by_test.items():

            long_form = self.is_long_form(test_type, instances)
            if long_form:
                serialised = {
                    'long_form'    : True,
                    'lab_test_type': test_type,
                    'count'        : len(instances),
                    'instances'    : [
                        self.serialise_long_form_instance(i) for i in instances
                    ]
                }
            else:
                serialised = {
                    'long_form'    : False,
                    'lab_test_type': test_type,
                    'count'        : len(instances),
                    'instances'    : self.serialise_tabular_instances(instances)
                }

            serialised_tests[test_type] = serialised

        return json_response(
            {
                'test_order': test_order,
                'tests'     : serialised_tests
            }
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
