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
]
