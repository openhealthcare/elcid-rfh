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
]

POSITIVE_TEST_VALUES = [
    '*****Amended Result*****~Detected',
    'DETECTED',
    'Detected',
    'Not Detected',
    'Not detected',
    'Not detected- PHE Ref Lab report (14/03/2020)',
    'POSITIVE',
    'POSITIVE~SARS CoV-2 RNA DETECTED. Please maintain~appropriate Infection Prevention and Control~Measures in line with PHE Guidance.',
    'SARS CoV-2 not detected - result from PHE',
    'detected',
    'detected~result from ref lab',
]

PENDING_TEST_VALUES = [
    'Pending',
]

OTHER_TEST_VALUES = [
    '.',
    '.{Not tested}',
    '.{}',
    '.{}Sample sent to Colindale',
    'Inappropriate sample. Not processed.',
    'Insufficient sample for testing',
    'Invalid',
    'No sample received in Virology.',
    'No sample received in Virology. - Not tested sent ~ to Colindale for testing.',
    'No sample received in Virology. ~ Not tested sent to Colindale for testing.',
    'Not tested',
    'Not tested sent to Colindale for testing.',
    'Not tested ~ Duplicate sample. Not processed',
    'Not tested ~ This patient has been previously tested for ~ SARS CoV2/COVID19 and does not fit the criteria ~ for repeat testing. ~ Please contact Microbiology if clinical concerns / ~ testing required.',
    'Not tested.',
    'Not tested. Sample leaked in transit.',
    'Not tested. See 20L095446',
    'Please refer to PHE Sample',
    'Please refer to PHE Sample.',
    'Please refer to PHE sample',
    'Please refer to PHE sample.',
    'Please see 20L083734 for results',
    'Please see sample 20K137549 from same date',
    'Refer to sample sent to PHE',
    'Sample inhibitory - no result',
    'Sample sent to Colindale',
    'Sample sent to Colindale.',
    'See 20L053902',
    'See 20L053910',
    'See 20L053930',
    'See 20L083732',
    'See 20L085854',
    'See Sample 20L073345',
    'See sample 20L047824',
    'Sent to Colindale for testing.',
    'This sample was repeatedly inhibitory to PCR. ~ Please send a repeat.',
    'This sample was repeatedly inhibitory to PCR.~Please send a repeat.',
    'To follow undetected',
    'inappropriate sample not tested',
    'test',
    'test no longer required, please cancel.',
]
