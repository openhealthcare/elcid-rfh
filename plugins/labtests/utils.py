from collections import OrderedDict, defaultdict


def clean_observation_name(obs_name):
    """
    Some obs names have trailing... as can be seen above
    so we remove them
    """
    return obs_name.rstrip(".")


def clean_observation_value(value):
    """
    "~" are used as new line charecters. They add in additional
    information that is just repeated in all lts of the type.

    Ie its just noise, e.g. ~Please note: New method effective.
    """
    if "~" in value:
        return value[:value.find("~")]
    else:
        return value


def recent_observations(patient, test_name_to_observation_names):
    """
    Takes in a patient and an ordered dictionary of test name
    to observations names.

    Returns the most recent observation of that test_name/observation name.

    If there most recent result is pending and there is a prior value
    it will return that value.

    The order of the result
    """
    tests = patient.lab_tests.filter(
        test_name__in=test_name_to_observation_names.keys()
    ).order_by("-datetime_ordered")
    by_observation = defaultdict(dict)

    for t in tests:
        tn = t.test_name
        for obs in t.observation_set.all():
            obs_name = obs.observation_name
            if obs_name in test_name_to_observation_names[tn]:
                if obs_name not in by_observation or by_observation[obs_name][
                    "observation_value"
                ] == "Pending":
                    by_observation[obs_name][
                        "observation_datetime"
                    ] = obs.observation_datetime
                    obs_value = clean_observation_value(obs.observation_value)
                    by_observation[obs_name]["observation_value"] = obs_value

    results_order = []
    for observation_names in test_name_to_observation_names.values():
        for observation_name in observation_names:
            results_order.append(observation_name)

    result = OrderedDict()

    for observation_name in results_order:
        if observation_name in by_observation:
            result[clean_observation_name(observation_name)] = by_observation[observation_name]
    return result


