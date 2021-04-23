"""
Covid specific urls
"""
from django.urls import path
from django.conf.urls import url

from plugins.covid import views

urlpatterns = [
    url(
        'templates/covid/dashboard.html',
        views.CovidDashboardView.as_view(),
        name='covid_dashboard'
    ),
    url(
        'covid/amt-dashboard/',
        views.CovidAMTDashboardView.as_view(),
        name='covid_amt_dashboard'
    ),
    url(
        'templates/covid/recent_positives.html',
        views.CovidRecentPositivesView.as_view(),
        name='covid_recent_positives'
    ),

    url(
        'covid/cohort-download/',
        views.CovidCohortDownloadView.as_view(),
        name='covid_download'
    ),
    url(
        'covid/extract-download/',
        views.CovidExtractDownloadView.as_view(),
        name='covid_extract_download'
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
        'covid/six-month-followup-letter/(?P<pk>\d+)/?$',
        views.CovidSixMonthFollowupLetter.as_view(),
        name='covid_followup_letter'
    ),
    path(
        'templates/covid/clinic_list.html',
        views.CovidClinicList.as_view(),
        name="covid_clinic_list"
    )

]
