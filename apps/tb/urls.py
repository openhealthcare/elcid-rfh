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
        r'^tb/latent_new_patient_assessment/(?P<pk>\d+)/?$',
        views.LatentNewPatientAssessment.as_view()
    ),
    url(
        r'^tb/follow_up_patient_assessment/(?P<pk>\d+)/?$',
        views.FollowUpPatientAssessment.as_view()
    ),
]
