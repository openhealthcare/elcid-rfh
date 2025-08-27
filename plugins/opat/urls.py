"""
Urls for the OPAT Opal plugin
"""
from django.conf.urls import url

from plugins.opat import views

urlpatterns = [
    url(
        r'^opat/opat_medication/$',
        views.OPATMedicationModal.as_view(),
        name="opat_medication_modal"
    ),

    url(
        r'opat/activity/(?P<year>\d+)/$',
        views.OPATActivityView.as_view(),
        name="opat_activity"
    ),


    url(
        r'opat/patients/(?P<year>\d+)/$',
        views.OPATPatientsView.as_view(),
        name="opat_patients"
    ),


]
