from collections import OrderedDict, defaultdict
import itertools
import re
from django.conf import settings
from opal.core.api import patient_from_pk, LoginRequiredViewset
from opal.core.views import json_response
from lab import models


def clean_ref_range(ref_range):
    return ref_range.replace("]", "").replace("[", "").strip()


def extract_observation_value(observation_value):
    """
        if an observation is numeric, return it as a float
        if its >12 return >12
        else return None
    """
    regex = r'^[-0-9][0-9.]*$'
    obs_result = observation_value.strip()
    obs_result = obs_result.split("~")[0].strip("<").strip(">").strip()
    if re.match(regex, obs_result):
        return round(float(obs_result), 3)


def is_empty_observation_value(self, observation_value):
    """ we don't care about empty strings or
        ' - ' or ' # '
    """
    if isinstance(observation_value, str):
        return not observation_value.strip().strip("-").strip("#").strip()
    else:
        return observation_value is None


def to_date_str(some_date):
    if some_date:
        return some_date[:10]


def datetime_to_str(dt):
    return dt.strftime(
        settings.DATETIME_INPUT_FORMATS[0]
    )


class InfectionTestSummary(LoginRequiredViewset):
    base_name = "infection_test_summary"
    RELEVANT_TESTS = OrderedDict((
        ("FULL BLOOD COUNT", ["WBC", "Lymphocytes", "Neutrophils"]),
        ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
        ("LIVER PROFILE", [
            "ALT", "AST", "Alkaline Phosphatase"
        ]),
    ),)

    def get_queryset_for_obs(self, patient, test_name, obs_name):
        """
        Returns all observations for a patient/lab_test/observation
        """
        return models.Obs.objects.filter(
            test__patient = patient
        ).filter(
            observation_name=obs_name
        ).filter(
            test__test_name=test_name
        ).order_by("-test__datetime_ordered")

    def get_observations(self, patient):
        """
        Looks at all the obs in relevant tests
        it returns the latest 6 dates we have results for
        """
        dates_to_obs = defaultdict(list)

        # get the latest 6 results for all observations
        for test_name, obs_names in self.RELEVANT_TESTS.items():
            for obs_name in obs_names:
                qs = self.get_queryset_for_obs(
                    patient, test_name, obs_name
                )[:5]
                for obs in qs:
                    dates_to_obs[obs.test.datetime_ordered].append(obs)

        # get the highest 6 results of all the observations
        recent_dates = sorted(dates_to_obs.keys())
        recent_dates = recent_dates[-5:]

        # for each observation we want an array of 6 corresponding
        # to the dates in recent dates, if there is no
        # observation for the date it should be empty
        obs_names = [i for i in itertools.chain(*self.RELEVANT_TESTS.values())]
        latest_results = defaultdict(dict)

        recent_dates_str = []

        for recent_date in recent_dates:
            recent_date_str = to_date_str(datetime_to_str(recent_date))
            recent_dates_str.append(recent_date_str)
            obs_name_to_obs = {o.observation_name: o for o in dates_to_obs[recent_date]}
            for obs_name in obs_names:
                obs = obs_name_to_obs.get(obs_name, None)

                # get a rounded float version
                if obs:
                    obs_value = extract_observation_value(obs.observation_value)
                    latest_results[obs_name][recent_date_str] = obs_value

        obs_values = []
        for obs_name in obs_names:
            obs_values.append({
                "name": obs_name,
                "latest_results": latest_results[obs_name]
            })
        return {"obs_values": obs_values, "recent_dates": recent_dates_str}


    @patient_from_pk
    def retrieve(self, request, patient):
        result = self.get_observations(patient)
        return json_response(result)


