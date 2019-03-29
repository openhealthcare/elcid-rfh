"""
Urls for the tb Opal plugin
"""
from django.conf.urls import url

from apps.tb import views

urlpatterns = [
    url(
        r'^tb/clinical_advice/(?P<pk>\d+)/?$',
        views.ClinicalAdvicePrintView.as_view()
    ),
    url(
        r'^tb/ltbi_initial_assessment/(?P<pk>\d+)/?$',
        views.LTBIInitialAssessment.as_view()
    ),
    url(
        r'^tb/ltbi_followup_assessment/(?P<pk>\d+)/?$',
        views.LTBIFollowUp.as_view()
    ),
    url(
        r'^tb/primary_diagnosis/$',
        views.PrimaryDiagnosisModal.as_view(),
        name="primary_diagnosis_modal"
    ),
    url(
        r'^tb/co_morbidities/$',
        views.SecondaryDiagnosisModal.as_view(),
        name="secondary_diagnosis_modal"
    ),
    url(
        r'^tb/tb_medication/$',
        views.TbMedicationModal.as_view(),
        name="tb_medication_modal"
    ),
    url(
        r'^tb/other_medication/$',
        views.OtherMedicationModal.as_view(),
        name="other_medication_modal"
    )
]
