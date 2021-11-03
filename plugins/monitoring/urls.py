"""
Urls for the monitoring plugin
"""
from django.conf.urls import url

from plugins.monitoring import views

urlpatterns = [
    url(
        'templates/monitoring/lab_timings.html',
        views.LabTimings.as_view(),
        name='lab_sync_dashboard'
    ),
    url(
        'templates/monitoring/system_stats.html',
        views.SystemStats.as_view(),
        name='system_stats_dashboard'
    ),
    url(
        'templates/monitoring/patient_information_load_stats.html',
        views.PatientInformationLoadStats.as_view(),
        name='patient_information_load_stats'
    ),
    url(
        'templates/monitoring/imaging_load_stats.html',
        views.ImagingLoadStats.as_view(),
        name='imaging_load_stats'
    ),
    url(
        'templates/monitoring/appointment_load_stats.html',
        views.AppointmentLoadStats.as_view(),
        name='appointment_load_stats'
    ),
    url(
        'templates/monitoring/admission_load_stats.html',
        views.AdmissionLoadStats.as_view(),
        name='admission_load_stats'
    ),
]
