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
        'Sodium',
        'Potassium',
        'Urea',
        'Creatinine'
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
        'Teicoplanin Level Result'
    ]
}

def valid_observation_value(value):
    """
    Predicate function to determine if this value should be skipped
    """
    if value.startswith('Regret'):
        return False
    if value.startswith('Sample'):
        return False
    return True


def get_opat_summmary_information(patient):
    """
    Given an OPAL patient, return an OPAT test summary for them.
    """
    result = {}
    observation_names = []

    for rows in RELEVANT_OBS_NAMES.values():
        for name in rows:
            result[name] = {}
            observation_names.append(name)

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

                as_date = obs.observation_datetime.date().strftime("%d/%m")

                # Sometimes we get complaints from the lab
                if valid_observation_value(obs.observation_value):

                    result[obs_name][as_date] = obs.observation_value
                    dates.add(as_date)

    return {
        'dates': sorted(list(dates)),
        'names': observation_names,
        'results': result
    }
