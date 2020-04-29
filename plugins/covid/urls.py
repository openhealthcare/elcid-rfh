"""
Covid specific urls
"""
from django.conf.urls import url

from plugins.covid import views

urlpatterns = [
    url(
        'templates/covid/dashboard.html',
        views.CovidDashboardView.as_view(),
        name='covid_dashboard'
    ),
    url(
        'covid/cohort-download/',
        views.CovidCohortDownloadView.as_view(),
        name='covid_download'
    ),
]
