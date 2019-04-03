from collections import OrderedDict, defaultdict


RELEVANT_TESTS = OrderedDict((
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
    Returns and ordered dict of observations in the order declared above.
    """
    tests = patient.labtest_set.filter(
        lab_test_type__istartswith="upstream"
    ).order_by("-datetime_ordered")
    by_observation = defaultdict(dict)

    for t in tests:
        tn = t.extras["test_name"]
        if tn in RELEVANT_TESTS:
            for o in t.extras["observations"]:
                on = o["observation_name"]
                if on in RELEVANT_TESTS[tn]:
                    by_observation[on]["observation_datetime"] = o[
                        "observation_datetime"
                    ]
                    obs_value = clean_observation_value(
                        o["observation_value"]
                    )
                    by_observation[on]["observation_value"] = obs_value
                    if len(by_observation) == len(RELEVANT_TESTS):
                        break

    results_order = []
    for ons in RELEVANT_TESTS.values():
        for on in ons:
            results_order.append(on)

    result = OrderedDict()

    for on in results_order:
        if on in by_observation:
            obs_name = clean_observation_name(on)
            result[obs_name] = by_observation[on]
    return result

