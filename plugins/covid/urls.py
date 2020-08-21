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
    url(
        'covid/letter/(?P<pk>\d+)/?$',
        views.CovidLetter.as_view(),
        name='covid_letter'
    ),
    url(
        'covid/followup-letter/(?P<pk>\d+)/?$',
        views.CovidFollowupLetter.as_view(),
        name='covid_followup_letter'
    ),
    url(
        'covid/upcoming_followups/$',
        views.CovidUpcomingFollowups.as_view(),
        name='covid_followup_clinic_list'
    ),
]
