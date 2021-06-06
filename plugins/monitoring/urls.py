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
        'templates/monitoring/demographics_load_stats.html',
        views.DemographicsLoadStats.as_view(),
        name='demographics_load_stats'
    )
]
