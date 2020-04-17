"""
Constants for the covid plugin
"""
COVID_ROLE = 'covid19'

CORONAVIRUS_TEST_NAME        = '2019 NOVEL CORONAVIRUS'
CORONAVIRUS_OBSERVATION_NAME = '2019 nCoV'

NEGATIVE_TEST_VALUES = [
    'NOT detected',
    'NOT detected ~ SARS CoV-2 RNA NOT Detected. ~ Please note that the testing of upper respiratory ~ tract specimens alone may not exclude SARS CoV-2 ~ infection. ~ If there is a high clinical index of suspicion, ~ please send a lower respiratory specimen (sputum, ~ BAL, EndoTracheal aspirate) to exclude SARS CoV-2 ~ where possible.',
    'NOT detected~SARS CoV-2 RNA NOT Detected.~Please note that the testing of upper respiratory~tract specimens alone may not exclude SARS CoV-2~infection.~If there is a high clinical index of suspicion,~please send a lower respiratory specimen (sputum,~BAL, EndoTracheal aspirate) to exclude SARS CoV-2~where possible.',
    'NOT detected~result from ref lab',
    'undetected',
    'UNDETECTED',
    'Undetectd',
    'Undetected',
    'Undetected - result from ref lab',
    'Undetected - results from ref lab',
    'Undetected~results form ref lab',
    'Undetected~results from ref lab',
    'Undetetced',
    'Not Detected',
    'Not detected',
    'Not detected- PHE Ref Lab report (14/03/2020)',
    'SARS CoV-2 not detected - result from PHE',
]

POSITIVE_TEST_VALUES = [
    '*****Amended Result*****~Detected',
    'DETECTED',
    'Detected',
    'POSITIVE',
    'POSITIVE~SARS CoV-2 RNA DETECTED. Please maintain~appropriate Infection Prevention and Control~Measures in line with PHE Guidance.',
    'detected',
    'detected~result from ref lab',
]

PENDING_TEST_VALUES = [
    'Pending',
]
