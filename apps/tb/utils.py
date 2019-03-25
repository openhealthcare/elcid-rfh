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
    ('HIV 1 + 2 ANTIBODIES', ['HIV 1 + 2 Antibodies..........'])
),)


def clean_observation_name(obs_name):
    """
    Some obs names have trailing... as can be seen above
    so we remove them
    """
    return obs_name.rstrip(".")


def clean_observation_value(value):
    """
    We remove all results that have a New method effective,
    these methods came into effect years ago and are just noise
    """
    TO_REMOVE = "~Please note: New method effective"
    if TO_REMOVE in value:
        return value[:value.find(TO_REMOVE)]
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
                    by_observation[on]["observation_datetime"] = o["observation_datetime"]
                    by_observation[on]["observation_value"] = clean_observation_value(
                        o["observation_value"]
                    )
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

