"""
Utilities for the OPAT Plugin
"""
import datetime

# Amikacin,

# Gentamicin
# GENTAMICIN LEVEL

# Teicoplannin Level
# TEICOPLANIN LEVEL

# VANCOMYCIN LEVEL / Vancomycin

RELEVANT_TEST_NAMES = [
    'FBC And Differential',
    'UE (RFH)',
    'Liver Profile',
    "C-Reactive Protein",
]

RELEVANT_OBS_NAMES = {
    'FBC And Differential': [
        'Haemoglobin (g/L)',
        'White cell count',
        'Platelet count',

    ],
    'UE (RFH)': [
        'Sodium mmol/L',
        'Potassium mmol/L',
        'Urea mmol/L',
        'Creatinine umol/L'
    ],
    'Liver Profile': [
        'Total Bilirubin',
        'Albumin',
        'Alanine Aminotransferase',
        'Alkaline Phosphatase'
    ],
    'C-Reactive Protein' :[
        'C-Reactive Protein'
    ],
    'Teicoplanin Level' : [
        'Teicoplanin Level Result mg/L'
    ]
}

def get_opat_summmary_information(patient):
    """
    Given an OPAL patient, return an OPAT test summary for them.
    """
    result = {}
    for rows in RELEVANT_OBS_NAMES.values():
        for name in rows:
            result[name] = {}

    dates = set()

    four_weeks_ago = datetime.datetime.now() - datetime.timedelta(days=4*7)
    tests = patient.lab_tests.filter(
        test_name__in=RELEVANT_TEST_NAMES,
        datetime_ordered__gt=four_weeks_ago
    ).prefetch_related('observation_set')

    for test in tests:
        for obs in test.observation_set.all():
            obs_name = obs.observation_name
            if obs_name in RELEVANT_OBS_NAMES[test.test_name]:

                as_date = obs.observation_datetime.date()

                result[obs_name][as_date] = obs.observation_value
                dates.add(as_date)

    return result
