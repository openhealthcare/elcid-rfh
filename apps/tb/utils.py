"""
Utilities for the TB module
"""
from collections import OrderedDict, defaultdict
from django.conf import settings


RELEVANT_TESTS = OrderedDict((
    ("AFB : CULTURE", ["TB: Culture Result"]),
    ("TB PCR TEST", ["TB PCR"]),
    ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
    ("LIVER PROFILE", ["ALT", "AST", "Total Bilirubin"]),
    ("QUANTIFERON TB GOLD IT", [
        "QFT IFN gamma result (TB1)",
        "QFT IFN gamme result (TB2)",
        "QFT TB interpretation"
    ]),
    ('HEPATITIS B SURFACE AG', ["Hepatitis B 's'Antigen........"]),
    ('HEPATITIS C ANTIBODY', ["Hepatitis C IgG Antibody......"]),
    ('HIV 1 + 2 ANTIBODIES', ['HIV 1 + 2 Antibodies..........']),
    ("25-OH Vitamin D", ["25-OH Vitamin D"]),
),)


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


def get_tb_summary_information(patient):
    """
    Returns an ordered dict of observations in the order declared above.
    """
    tests = patient.lab_tests.filter(
        test_name__in=RELEVANT_TESTS.keys()
    ).order_by("-datetime_ordered")
    by_observation = defaultdict(dict)

    for t in tests:
        tn = t.test_name
        for obs in t.observation_set.all():
            obs_name = obs.observation_name
            if obs_name in RELEVANT_TESTS[tn]:
                if obs_name not in by_observation or by_observation[obs_name][
                    "observation_value"
                ] == "Pending":
                    by_observation[obs_name][
                        "observation_datetime"
                    ] = obs.observation_datetime
                    obs_value = clean_observation_value(obs.observation_value)
                    by_observation[obs_name]["observation_value"] = obs_value

    results_order = []
    for observation_names in RELEVANT_TESTS.values():
        for observation_name in observation_names:
            results_order.append(observation_name)

    result = OrderedDict()

    for observation_name in results_order:
        if observation_name in by_observation:
            result[clean_observation_name(observation_name)] = by_observation[observation_name]
    return result
