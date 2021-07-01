"""
Urls for the tb Opal plugin
"""
from django.conf.urls import url

from plugins.tb import views

urlpatterns = [
    url(
        r'^tb/clinical_advice/(?P<pk>\d+)/?$',
        views.ClinicalAdvicePrintView.as_view()
    ),
    url(
        r'^tb/initial_assessment/(?P<pk>\d+)/?$',
        views.InitialAssessment.as_view()
    ),
    url(
        r'^tb/followup_assessment/(?P<pk>\d+)/?$',
        views.FollowUp.as_view()
    ),
    url(
        r'^tb/nurse_letter/(?P<pk>\d+)/?$',
        views.NurseLetter.as_view(),
        name="nurse_letter"
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
    ),
    url(
        r'^templates/tb/clinic_list.html$',
        views.ClinicList.as_view(),
        name="tb_clinic_list"
    ),
    url(
        r'^templates/tb/last_30_days.html$',
        views.Last30Days.as_view(),
        name="last_30_days"
    ),
    url(
        r'^tb/patient_consultation_print/(?P<pk>\d+)/?$',
        views.PrintConsultation.as_view()
    ),
    url(
        r'^templates/tb/mdt_list.html$',
        views.MDTListOld.as_view(),
        name="mdt_list"
    ),
    url(
        r'^templates/tb/mdt_list/(?P<site>[0-9a-zA-Z_\-]+)/$',
        views.MDTList.as_view(),
        name="mdt_list"
    )
]
