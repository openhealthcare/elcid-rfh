from collections import OrderedDict, defaultdict


RELEVANT_TESTS = OrderedDict((
    ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
    ("LIVER PROFILE", ["ALT", "AST", "Total Bilirubin"]),
    ("QUANTIFERON TB GOLD IT", [
        "QFT IFN gamma result (TB1)",
        "QFT IFN gamma result (TB2)",
    ]),
    ('HEPATITIS B SURFACE AG', ["Hepatitis B 's'Antigen........"]),
    ('HEPATITIS C ANTIBODY', ["Hepatitis C IgG Antibody......"]),
    ('HIV 1 + 2 ANTIBODIES', ['HIV 1 + 2 Antibodies..........'])
),)



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
                    by_observation[on]["observation_value"] = o["observation_value"]
                    if len(by_observation) == len(RELEVANT_TESTS):
                        break

    results_order = []
    for ons in RELEVANT_TESTS.values():
        for on in ons:
            results_order.append(on)


    result = OrderedDict()

    for on in results_order:
        if on in by_observation:
            result[on] = by_observation[on]
    return result

