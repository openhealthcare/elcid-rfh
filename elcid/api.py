"""
API endpoints for the elCID application
"""
from collections import defaultdict, OrderedDict

from django.conf import settings
from django.http import HttpResponseBadRequest
from rest_framework import viewsets, status
from opal.core.api import item_from_pk, router as opal_router
from opal.core.api import (
    OPALRouter, patient_from_pk, LoginRequiredViewset, SubrecordViewSet
)
from opal.core.views import json_response
from opal.core import serialization
from opal.models import Tagging

from elcid import patient_lists
from intrahospital_api import loader, epr
from plugins.covid import lab as covid_lab
from plugins.labtests import models as lab_test_models
from plugins.labtests import constants as lab_constants

from elcid import models as emodels
from plugins.tb import models as tb_models


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
    basename = 'lab_test_results_view'

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

        # we have some lab tests with no datetime ordered
        # they also have no lab test name or observation
        # value so skipping them
        lab_tests = lab_tests.exclude(
            datetime_ordered=None
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

    def display_class_for_observation(self, observation):
        """
        Returns too-high too-low or '' for a numeric observation
        """
        display_class = ''
        numeric       = observation.value_numeric
        refrange      = observation.cleaned_reference_range

        if refrange is None or numeric is None:
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
        observation_units  = {}
        lab_numbers        = {}
        data               = defaultdict(lambda: defaultdict(lambda: None))
        departments         = set()

        for instance in instances:
            test_datetimes.add(instance.datetime_ordered)
            lab_numbers[serialization.serialize_datetime(instance.datetime_ordered)] = instance.lab_number
            departments.add(instance.department)

            for observation in instance.observation_set.all():
                name = observation.observation_name.rstrip('.')
                if not self.is_empty_value(observation.observation_value):

                    if name not in observation_ranges:
                        if observation.reference_range != " -":
                            observation_ranges[name] = observation.reference_range

                    if name not in observation_units:
                        observation_units[name] = observation.units

                    observation_names.add(name)
                    data[name][serialization.serialize_datetime(instance.datetime_ordered)] = {
                        'value'        : observation.observation_value,
                        'range'        : observation.reference_range,
                        'display_class': self.display_class_for_observation(observation)
                    }


        date_series = list(sorted(test_datetimes))
        date_series = [serialization.serialize_datetime(d) for d in date_series]

        return {
            'test_datetimes'    : date_series[-8:],
            'observation_names' : list(sorted(observation_names)),
            'lab_numbers'       : lab_numbers,
            'observation_ranges': observation_ranges,
            'observation_units' : observation_units,
            'observation_series': data,
            'departments'       : list(departments),
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
                        'value': o.observation_value,
                        'units': o.units
                    }
                )
        return {
            'lab_number'        : instance.lab_number,
            'date'              : instance.datetime_ordered,
            'observations'      : serialised_observations,
            'site'              : instance.cleaned_site,
            'department'        : instance.department
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
                'tests'     : serialised_tests,
                'departments': list(lab_constants.WITHPATH_DEPATMENT_MAPPING.values())
            }
        )


class InfectionServiceTestSummaryApi(LoginRequiredViewset):
    basename = 'infection_service_summary_api'
    RELEVANT_TESTS = OrderedDict((
        ("FULL BLOOD COUNT", ["WBC", "Lymphocytes", "Neutrophils"],),
        ("CLOTTING SCREEN", ["INR"],),
        ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
        ("LIVER PROFILE", ["ALT", "AST", "Alkaline Phosphatase"]),
        ("PROCALCITONIN", ["Procalcitonin"]),
    ),)

    ANTIFUNGAL_TESTS = OrderedDict((
        ("BETA D GLUCAN TEST", [
            "Beta Glucan test:",
            "Beta Glucan concentration",
            "Beta Glucan conc. (pg/mL)",
        ]),
        ("GALACTOMANNAN AGN. ELISA", ["Galactomannan Agn. ELISA", "Galactomannan Agn. INDEX"])
    ))

    ANTIFUNGAL_SHORT_NAMES = {
        "BETA D GLUCAN TEST": "Beta D Glucan",
        "GALACTOMANNAN AGN. ELISA": "Galactomannan",
        "Beta Glucan test:": "",
        "Beta Glucan conc. (pg/mL)": "Concentration (pg/mL)",
        "Beta Glucan concentration": "Concentration",
        "Galactomannan Agn. ELISA": "Agn. ELISA",
        "Galactomannan Agn. INDEX": "Agn. INDEX"
    }

    NUM_RESULTS = 5


    def _get_antifungal_ticker_dict(self, test):
        """
        Given a lab test instance, return a dict in the lab results ticker format
        """
        observations = test.observation_set.all()

        timestamp = observations[0].observation_datetime
        test_name = test.test_name

        result_string = ''

        for observation in observations:

            if observation.observation_name in self.ANTIFUNGAL_TESTS[test_name]:
                result_string += ' {} {}'.format(
                    self.ANTIFUNGAL_SHORT_NAMES[observation.observation_name],
                    observation.observation_value.split('~')[0]
                )

        display_name = '{} {}'.format(
            self.ANTIFUNGAL_SHORT_NAMES[test_name],
            test.site.replace('&', ' ').split(' ')[0]
        )


        return {
            'date_str' : timestamp.strftime('%d/%m/%Y %H:%M'),
            'timestamp': timestamp,
            'name'     : display_name,
            'value'    : result_string.strip()
        }

    def get_antifungal_observations(self, patient):
        """
        If the patient is on the chronic or acute antifungal lists, add some observations.

        Specifically up to 3 per sample site for the tests in self.ANTIFUNGAL_TESTS
        """
        ticker = []

        is_antifungal = Tagging.objects.filter(
            episode__patient=patient, archived=False, value=patient_lists.Antifungal.tag).exists()

        if not is_antifungal:
            antifungal_episodes = emodels.ChronicAntifungal.antifungal_episodes()
            is_antifungal = antifungal_episodes.filter(
                patient=patient
            ).exists()

        if is_antifungal:

            ticker_test_counts = defaultdict(int)

            for test_name in self.ANTIFUNGAL_TESTS:
                data = []
                tests = lab_test_models.LabTest.objects.filter(
                    test_name=test_name, patient=patient
                ).order_by('-datetime_ordered')

                for test in tests:
                    test_tuple = (test.test_name, test.site.replace('&', ' ').split(' ')[0])

                    if ticker_test_counts[test_tuple] < 3:
                        ticker_test_counts[test_tuple] += 1
                        ticker.append(self._get_antifungal_ticker_dict(test))

        return ticker


    def get_ticker_observations(self, patient):
        """
        Some results are displayed as a ticker in chronological
        order.
        """
        ticker =  covid_lab.get_covid_result_ticker(patient)
        ticker += self.get_antifungal_observations(patient)
        ticker = list(reversed(sorted(ticker, key=lambda i: i['timestamp'])))

        return ticker

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

        for i in qs:
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
        ).exclude(
            observation_datetime=None
        ).order_by(
            "-observation_datetime"
        ).select_related(
            'test'
        )

    def get_PROCALCITONIN_Procalcitonin(self, observation):
        return observation.observation_value.split('~')[0]

    def get_observation_value(self, observation):
        """
        Return the observation value for this observation

        Defaults to .value_numeric, but looks for a method
        called get_TEST_NAME_OBSERVATION_NAME(observation)
        and uses that if it exists.
        """
        method_name = 'get_{}_{}'.format(
            observation.test.test_name, observation.observation_name
        )
        if hasattr(self, method_name):
            return getattr(self, method_name)(observation)
        return observation.value_numeric

    def serialize_observations(self, observations):
        latest_results = {
            serialization.serialize_date(i.observation_datetime.date()): self.get_observation_value(i)
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
            recent_dates=recent_dates,
            ticker=self.get_ticker_observations(patient)
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
    basename = "upstream_blood_culture_results"

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
    basename = 'demographics_search'
    PATIENT_FOUND_IN_ELCID = "patient_found_in_elcid"
    PATIENT_FOUND_UPSTREAM = "patient_found_upstream"
    PATIENT_NOT_FOUND = "patient_not_found"

    def list(self, request, *args, **kwargs):
        hospital_number = request.query_params.get("hospital_number", "")
        # We should never have hospital numbers prefixed with 0
        # as VIEW_CRS_Patient_Masterfile does not.
        hospital_number = hospital_number.lstrip('0')
        if not hospital_number:
            return HttpResponseBadRequest("Please pass in a hospital number")
        demographics = emodels.Demographics.objects.filter(
            hospital_number=hospital_number
        ).last()

        # If we can't find a patient in demographics
        # check to see if it is an inactive MRN that
        # has been merged with a different MRN on elcid
        if not demographics:
            merged_mrn = emodels.MergedMRN.objects.filter(
                mrn=hospital_number
            ).first()
            if merged_mrn:
                demographics = merged_mrn.patient.demographics()


        # the patient is in elcid
        if demographics:
            return json_response(dict(
                patient=demographics.patient.to_dict(request.user),
                status=self.PATIENT_FOUND_IN_ELCID
            ))
        # ignore these hospital numbers as they always belong to a different hospital
        elif hospital_number.startswith("RAN") and hospital_number.strip("RAN").isnumeric():
            return json_response(dict(status=self.PATIENT_NOT_FOUND))
        else:
            if settings.USE_UPSTREAM_DEMOGRAPHICS:
                demographics = loader.search_upstream_demographics(hospital_number)
                if demographics:
                    return json_response(dict(
                        patient=dict(demographics=[demographics]),
                        status=self.PATIENT_FOUND_UPSTREAM
                    ))
        return json_response(dict(status=self.PATIENT_NOT_FOUND))


class BloodCultureIsolateApi(SubrecordViewSet):
    model = emodels.BloodCultureIsolate
    basename = emodels.BloodCultureIsolate.get_api_name()

    def create(self, request):
        bc = self.model()
        bc.update_from_dict(request.data, request.user)
        return json_response(
            bc.to_dict(request.user),
            status_code=status.HTTP_201_CREATED
        )


class AddToServiceViewSet(LoginRequiredViewset):
    basename = 'add_to_service'

    @patient_from_pk
    def update(self, request, patient):
        patient.create_episode(category_name=request.data['category_name'])
        return json_response({
            'status_code': status.HTTP_202_ACCEPTED
        })


class AbstractSendUpstreamViewSet(LoginRequiredViewset):

    @item_from_pk
    def update(self, request, item):

        epr.write_clinical_advice(item)

        return json_response({
            'status_code': status.HTTP_202_ACCEPTED
        })


class SendMicroBiologyUpstream(AbstractSendUpstreamViewSet):
    basename = "send_upstream"
    model = emodels.MicrobiologyInput


class SendPatientConsultationUpstream(AbstractSendUpstreamViewSet):
    basename = "send_pc_upstream"
    model = tb_models.PatientConsultation


elcid_router = OPALRouter()
elcid_router.register(
    UpstreamBloodCultureApi.basename, UpstreamBloodCultureApi
)
elcid_router.register(DemographicsSearch.basename, DemographicsSearch)
elcid_router.register(BloodCultureIsolateApi.basename, BloodCultureIsolateApi)

lab_test_router = OPALRouter()
lab_test_router.register(
    'infection_service_summary_api', InfectionServiceTestSummaryApi
)
lab_test_router.register('lab_test_results_view', LabTestResultsView)


opal_router.register('add_to_service', AddToServiceViewSet)
opal_router.register(SendMicroBiologyUpstream.basename, SendMicroBiologyUpstream)
opal_router.register(
    SendPatientConsultationUpstream.basename,
    SendPatientConsultationUpstream
)
