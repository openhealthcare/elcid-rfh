"""
Views for our covid plugin
"""
from django.views.generic import TemplateView
from opal.models import Patient

from elcid import patient_lists

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
]

POSITIVE_RESULTS = [
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

PENDING_RESULTS = [
    'Pending',
]

OTHER_RESULTS = [
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


class CovidDashboardView(TemplateView):
    template_name = 'covid/dashboard.html'

    def get_context_data(self, *a, **k):
        context = super(CovidDashboardView, self).get_context_data(*a, **k)

        tested = Patient.objects.filter(
            lab_tests__test_name='2019 NOVEL CORONAVIRUS').distinct()

        positive = tested.filter(
            lab_tests__observation__observation_value__in=POSITIVE_RESULTS
        )
        positive_ids = [p.id for p in positive]

        negative = tested.filter(
            lab_tests__observation__observation_value__in=NEGATIVE_RESULTS
        ).exclude(id__in=positive_ids)

        context['patients_tested'] = tested.count()
        context['positive_count'] = positive.count()
        context['negative_count'] = negative.count()

        context['icu_south_count'] = patient_lists.ICU().get_queryset().count()
        context['icu_east_count'] = patient_lists.ICUEast().get_queryset().count()
        context['icu_west_count'] = patient_lists.ICUWest().get_queryset().count()

        context['shdu_count'] = patient_lists.ICUSHDU().get_queryset().count()

        context['non_canonical_icu_count'] = patient_lists.NonCanonicalICU().get_queryset().count()
        context['icu_total'] = sum([
            context['icu_south_count'],
            context['icu_east_count'],
            context['icu_west_count'],
            context['shdu_count'],
            context['non_canonical_icu_count']
        ])
        context['covid_non_icu_count'] = patient_lists.Covid19NonICU().get_queryset().count()

        return context
