import datetime
from operator import itemgetter
from collections import defaultdict
from django.conf import settings
from django.utils.text import slugify
from django.http import Http404
from intrahospital_api import get_api


from rest_framework import viewsets
from opal.core.api import OPALRouter
from opal.core.api import patient_from_pk, LoginRequiredViewset
from opal.core.views import json_response
from elcid import models as emodels
from elcid.utils import timing


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


def refresh_lab_tests(patient, user):
    emodels.HL7Result.objects.filter(patient=patient).delete()
    api = get_api()
    hospital_number = patient.demographics_set.first().hospital_number
    results = api.results_for_hospital_number(hospital_number)
    for result in results:
        result["patient_id"] = patient.id
        hl7_result = emodels.HL7Result()
        hl7_result.update_from_dict(result, user)


def generate_time_series(observations):
    """
        take in a bunch of observations and return a list
        of numeric observation values
        If we can't pass the observation to a float, we skip it.
    """
    timeseries = []
    for observation in observations:
        obs_result = get_observation_value(observation)

        if obs_result:
            timeseries.append(obs_result)

    return timeseries


def extract_observation_value(observation_value):
    """
        if an observation is numeric, return it as a float
        if its >12 return >12
        else return None
    """
    obs_result = observation_value.split("~")[0]
    try:
        # we return None if its not numeric
        return float(obs_result)
    except ValueError:
        try:
            float(obs_result.strip("<").strip(">").strip())
            return obs_result
        except ValueError:
            return None


def get_observation_value(observation):
    return extract_observation_value(observation["observation_value"])


def clean_ref_range(ref_range):
    return ref_range.replace("]", "").replace("[", "").strip()


def get_reference_range(observation):
    ref_range = clean_ref_range(observation["reference_range"])
    if not len(ref_range.replace("-", "").strip()):
        return None
    range_min_max = ref_range.split("-")
    if len(range_min_max) > 2:
        return None
    return {"min": range_min_max[0].strip(), "max": range_min_max[1].strip()}


AEROBIC = "aerobic"
ANAEROBIC = "anaerobic"


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

    @patient_from_pk
    def retrieve(self, request, patient):
        found_observations = []
        observation_slug = request.query_params["observation"]
        for lab_test in patient.labtest_set.filter(
            lab_test_type=emodels.HL7Result.get_display_name()
        ):
            lab_test_type = lab_test.extras.get(
                "test_name", lab_test.lab_test_type
            )
            if slugify(lab_test_type) == request.query_params["labtest"]:
                existing_observations = lab_test.extras.get("observations", [])

                for existing_observation in existing_observations:
                    sluged_test_name = slugify(
                        existing_observation.get("test_name", None)
                    )
                    if sluged_test_name == observation_slug:
                        if lab_test.datetime_ordered:
                            existing_observation["datetime_ordered"] = lab_test.datetime_ordered
                            found_observations.append(existing_observation)

        if not found_observations:
            raise Http404
        collection = ObservationCollection(found_observations)
        return json_response(collection.to_dict())


class LabTestJsonDumpView(LoginRequiredViewset):
    base_name = 'lab_test_json_dump_view'

    @patient_from_pk
    def retrieve(self, request, patient):
        lab_tests = emodels.HL7Result.objects.filter(patient=patient)
        lab_tests = sorted(lab_tests, key=lambda x: x.extras.get("profile_description"))
        return json_response(
            dict(
                tests=[i.dict_for_view(None) for i in lab_tests]
            )
        )


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
        if some_date:
            return some_date[:10]

    def aggregate_observations_by_lab_test(self, lab_tests):
        by_test = defaultdict(list)
        # lab tests are sorted by lab test type
        # this is either the lab test type if its a lab test we've
        # defined or its what is in the profile description
        # if its an HL7 jobby
        for lab_test in lab_tests:
            as_dict = lab_test.dict_for_view(None)
            observations = as_dict.get("observations", [])
            lab_test_type = as_dict["extras"].get(
                "test_name", lab_test.lab_test_type
            )

            for observation in observations:
                obs_result = extract_observation_value(observation["observation_value"])
                if obs_result:
                    observation["observation_value"] = obs_result

                observation["reference_range"] = observation["reference_range"].replace("]", "").replace("[", "")
                if not len(observation["reference_range"].replace("-", "").strip()):
                    observation["reference_range"] = None
                else:
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

                observation["datetime_ordered"] = lab_test.datetime_ordered
                by_test[lab_test_type].append(observation)

        return by_test

    def is_empty_value(self, observation_value):
        """ we don't care about empty strings or
            ' - '
        """
        if isinstance(observation_value, str):
            return not observation_value.strip().strip("-").strip()
        else:
            return observation_value is None

    @patient_from_pk
    def retrieve(self, request, patient):
        # so what I want to return is all observations to lab test desplay
        # name with the lab test properties on the observation

        six_months_ago = datetime.date.today() - datetime.timedelta(6*30)
        lab_tests = emodels.HL7Result.objects.filter(patient=patient)
        lab_tests = lab_tests.filter(datetime_ordered__gte=six_months_ago)
        by_test = self.aggregate_observations_by_lab_test(lab_tests)
        serialised_tests = []

        # within the lab test observations should be sorted by test name
        # and within the if we have a date range we want to be exposing
        # them as part of a time series, ie adding in blanks if they
        # aren't populated
        for lab_test_type, observations in by_test.items():
            observations = sorted(observations, key=lambda x: x["datetime_ordered"])
            observations = sorted(observations, key=lambda x: x["observation_name"])

            # observation_time_series = defaultdict(list)
            by_observations = defaultdict(list)
            timeseries = {}

            observation_metadata = {}

            observation_date_range = {
                self.to_date_str(observation["observation_datetime"]) for observation in observations
            }
            observation_date_range = sorted(list(observation_date_range))
            long_form = False

            for observation in observations:
                test_name = observation["observation_name"]

                if test_name.strip() == "Haem Lab Comment":
                    # skip these for the time being, we may not even
                    # have to bring them in
                    continue

                # arbitrary but fine for prototyping, should we show it in a
                # table
                if isinstance(observation["observation_value"], (str, unicode,)):
                    if extract_observation_value(observation["observation_value"].strip(">").strip("<")) is None:
                        long_form = True

                if test_name not in by_observations:
                    obs_for_test_name = {
                        self.to_date_str(i["observation_datetime"]): i for i in observations if i["observation_name"] == test_name
                    }
                    # if its all None's for a certain observation name lets skip it
                    # ie if WBC is all None, lets not waste the users' screen space
                    # sometimes they just have '-' so lets skip these too
                    if not all(i for i in obs_for_test_name.values() if self.is_empty_value(i)):
                        continue
                    by_observations[test_name] = obs_for_test_name

                if test_name not in observation_metadata:
                    observation_metadata[test_name] = dict(
                        units=observation["units"],
                        reference_range=observation["reference_range"],
                        api_name=slugify(observation["observation_name"])
                    )

            serialised_lab_test = dict(
                long_form=long_form,
                timeseries=timeseries,
                api_name=slugify(lab_test_type),
                observation_metadata=observation_metadata,
                lab_test_type=lab_test_type,
                observations=observations,
                observation_date_range=observation_date_range,
                # observation_time_series=observation_time_series,
                by_observations=by_observations,
                observation_names=sorted(by_observations.keys()),
                tags=LAB_TEST_TAGS.get(lab_test_type, [])
            )
            serialised_tests.append(serialised_lab_test)

            serialised_tests = sorted(serialised_tests, key=itemgetter("lab_test_type"))

        all_tags = _LAB_TEST_TAGS.keys()

        return json_response(
            dict(
                tags=all_tags,
                tests=serialised_tests
            )
        )


class LabTestSummaryApi(LoginRequiredViewset):
    """
        The API View used in the card list. Returns the last 3 months (approixmately)
        of the tests we care about the most.
    """
    base_name = 'lab_test_summary_api'

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

    def aggregate_observations(self, patient):
        """
            takes the specific test/observations
            aggregates them by lab test, observation name
            adds the lab test datetime ordered to the observation dict
            sorts the observations by datetime ordered
        """
        test_data = emodels.HL7Result.get_relevant_tests(patient)
        result = defaultdict(lambda: defaultdict(list))
        relevant_tests = {
            "C REACTIVE PROTEIN": ["C Reactive Protein"],
            "FULL BLOOD COUNT": ["WBC", "Lymphocytes", "Neutrophils"],
            "LIVER PROFILE": ["ALT", "AST", "Alkaline Phosphatase"],
            "CLOTTING SCREEN": ["INR"]
        }

        for test in test_data:
            test_name = test.extras.get("profile_description")
            if test_name in relevant_tests:
                relevent_observations = relevant_tests[test_name]

                for observation in test.extras["observations"]:
                    observation_name = observation["test_name"]
                    if observation_name in relevent_observations:
                        observation["datetime_ordered"] = test.datetime_ordered
                        result[test_name][observation_name].append(observation)

        for test, obs_collection in result.items():
            for obs_name, obs in obs_collection.items():
                result[test][obs_name] = sorted(obs, key=lambda x: x["datetime_ordered"])

        return result

    def datetime_to_str(self, dt):
        return dt.strftime(
            settings.DATETIME_INPUT_FORMATS[0]
        )

    @timing
    def serialise_lab_tests(self, patient):
        aggregated_data = self.aggregate_observations(patient)

        serialised_obvs = []
        all_dates = set()

        for test_name, obs_collection in aggregated_data.items():
            for observation_name, observations in obs_collection.items():
                serialised_obvs.append(dict(
                    name=observation_name,
                    graph_values=generate_time_series(observations),
                    units=observations[0]["units"],
                    reference_range=get_reference_range(observations[0]),
                    latest_results={
                        self.datetime_to_str(i["datetime_ordered"]): get_observation_value(i) for i in observations if get_observation_value(i)
                    }
                ))
                all_dates = all_dates.union(
                    i["datetime_ordered"] for i in observations if get_observation_value(i)
                )

        recent_dates = sorted(list(all_dates))[-3:]
        obs_values = sorted(serialised_obvs, key=self.sort_observations)
        result = dict(
            obs_values=obs_values,
            recent_dates=recent_dates
        )

        return result

    @patient_from_pk
    def retrieve(self, request, patient):
        result = self.serialise_lab_tests(patient)
        return json_response(result)


class BloodCultureResultApi(viewsets.ViewSet):
    base_name = 'blood_culture_results'

    BLOOD_CULTURES = [
        emodels.GramStain.get_display_name(),
        emodels.QuickFISH.get_display_name(),
        emodels.GPCStaph.get_display_name(),
        emodels.GPCStrep.get_display_name(),
        emodels.GNR.get_display_name(),
        emodels.BloodCultureOrganism.get_display_name()
    ]

    def sort_by_date_ordered_and_lab_number(self, some_keys):
        """ takes in a tuple of (date, lab number)
            both date or lab number will be "" if empty

            it sorts them by most recent and lowest lab number
        """
        def comparator(some_key):
            dt = some_key[0]
            if not dt:
                dt = datetime.date.max
            return (dt, some_key[1],)
        return sorted(some_keys, key=comparator, reverse=True)

    def sort_by_lab_test_order(self, some_results):
        """
            results should be sorted by the order of the blood culture
            list
        """
        return sorted(
            some_results, key=lambda x: self.BLOOD_CULTURES.index(
                x["lab_test_type"]
            )
        )

    def translate_date_to_string(self, some_date):
        if not some_date:
            return ""

        dt = datetime.datetime(
            some_date.year, some_date.month, some_date.day
        )
        return dt.strftime(
            settings.DATE_INPUT_FORMATS[0]
        )

    @patient_from_pk
    def retrieve(self, request, patient):
        lab_tests = patient.labtest_set.filter(
            lab_test_type__in=self.BLOOD_CULTURES
        )
        lab_tests = lab_tests.order_by("datetime_ordered")
        cultures = defaultdict(lambda: defaultdict(dict))
        culture_order = set()

        for lab_test in lab_tests:
            lab_number = lab_test.extras.get("lab_number", "")
            # if lab number is None or "", group it together
            if not lab_number:
                lab_number = ""
            if lab_test.datetime_ordered:
                date_ordered = self.translate_date_to_string(
                    lab_test.datetime_ordered.date()
                )

                culture_order.add((
                    lab_test.datetime_ordered.date(), lab_number,
                ))
            else:
                date_ordered = ""
                culture_order.add(("", lab_number,))

            if lab_number not in cultures[date_ordered]:
                cultures[date_ordered][lab_number][AEROBIC] = defaultdict(list)
                cultures[date_ordered][lab_number][ANAEROBIC] = defaultdict(
                    list
                )

            isolate = lab_test.extras["isolate"]

            if lab_test.extras[AEROBIC]:
                cultures[date_ordered][lab_number][AEROBIC][isolate].append(
                    lab_test.to_dict(self.request.user)
                )
            else:
                cultures[date_ordered][lab_number][ANAEROBIC][isolate].append(
                    lab_test.to_dict(request.user)
                )

        culture_order = self.sort_by_date_ordered_and_lab_number(culture_order)

        for dt, lab_number in culture_order:
            dt_string = self.translate_date_to_string(dt)
            by_date_lab_number = cultures[dt_string][lab_number]
            for robic in [AEROBIC, ANAEROBIC]:
                for isolate in by_date_lab_number[robic].keys():
                    by_date_lab_number[robic][isolate] = self.sort_by_lab_test_order(
                        by_date_lab_number[robic][isolate]
                    )

        return json_response(dict(
            cultures=cultures,
            culture_order=culture_order
        ))


class DemographicsSearch(LoginRequiredViewset):
    base_name = 'demographics_search'
    PATIENT_FOUND_IN_ELCID = "patient_found_in_elcid"
    PATIENT_FOUND_UPSTREAM = "patient_found_upstream"
    PATIENT_NOT_FOUND = "patient_not_found"

    def retrieve(self, request, *args, **kwargs):
        hospital_number = kwargs["pk"]
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
                api = get_api()
                demographics = api.demographics(hospital_number)

                if demographics:
                    return json_response(dict(
                        patient=dict(demographics=[demographics]),
                        status=self.PATIENT_FOUND_UPSTREAM
                    ))
        return json_response(dict(status=self.PATIENT_NOT_FOUND))



elcid_router = OPALRouter()
elcid_router.register(BloodCultureResultApi.base_name, BloodCultureResultApi)
elcid_router.register(DemographicsSearch.base_name, DemographicsSearch)

lab_test_router = OPALRouter()
lab_test_router.register('lab_test_summary_api', LabTestSummaryApi)
lab_test_router.register('lab_test_results_view', LabTestResultsView)
lab_test_router.register(
    'lab_test_observation_detail', LabTestObservationDetail
)
lab_test_router.register('lab_test_json_dump_view', LabTestJsonDumpView)
