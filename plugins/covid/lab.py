"""
Helpers for working with Covid 19 testing
"""

class CovidTest(object):
    TEST_NAME        = None
    OBSERVATION_NAME = None
    POSITIVE_RESULTS = []
    NEGATIVE_RESULTS = []

    @classmethod
    def resulted_values(klass):
        values = []
        values += klass.POSITIVE_RESULTS
        values += klass.NEGATIVE_RESULTS
        return values


class Coronavirus2019Test(CovidTest):
    TEST_NAME        = '2019 NOVEL CORONAVIRUS'
    OBSERVATION_NAME = '2019 nCoV'

    POSITIVE_RESULTS = [
        '*****Amended Result*****~Detected',
        'DETECTED',
        'Detected',
        'POSITIVE',
        'POSITIVE~SARS CoV-2 RNA DETECTED. Please maintain~appropriate Infection Prevention and Control~Measures in line with PHE Guidance.',
        'detected',
        'detected~result from ref lab',
    ]

    NEGATIVE_RESULTS = [
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


class CrickInstituteTest(CovidTest):
    TEST_NAME        = 'CORONAVIRUS CRICK INST'
    OBSERVATION_NAME = 'SARS CoV-2 RNA'

    POSITIVE_RESULTS = [
        'POSITIVE'
    ]

    NEGATIVE_RESULTS = [
        'NOT detected'
    ]


class ReferenceLabTest(CovidTest):
    TEST_NAME        = 'CORONAVIRUS REF LAB'
    OBSERVATION_NAME = 'SARS CoV-2 RNA'

    POSITIVE_RESULTS = [
        'POSITIVE',
        'Detected',
        'Detected~ ~2019 nCoV ORF1ab Detected (Ct value: 20-30)~Please note, the Ct value for detection of SARS~CoV-2 viral RNA are indicative of the viral load~in the sample, but are not quantitative PCR~values. The Ct values obtained should therefore be~interpreted with caution.~SARS CoV-2 Detected in this sample'
    ]

    NEGATIVE_RESULTS = [
        'Undetected~ ~2019 nCoV ORF1ab Undetected~SARS CoV-2 Not detected in this sample',
        'Undetected~ ~2019 nCoV ORF1ab Undetected~SARS Co-2 Not detected in this sample',
        'NOT detected',
        'Undetected'
    ]
