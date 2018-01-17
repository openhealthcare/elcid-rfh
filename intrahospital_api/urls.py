"""
Urls for the intrahospital_api plugin
"""
from django.conf.urls import url

from intrahospital_api import views

urlpatterns = [
    url(
        r'^intrahospital_api/raw/results/(?P<hospital_number>[ 0-9A-Za-z_\-]+)$',
        views.IntrahospitalRawResultsView.as_view(),
        name="raw_results"
    ),
    url(
        r'^intrahospital_api/cooked/results/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalCookedResultsView.as_view(),
        name="cooked_results"
    ),
    url(
        r'^intrahospital_api/cooked/results/(?P<hospital_number>[0-9A-Za-z_\-]+)/json$',
        views.results_as_json,
        name="cooked_json_view"
    ),
    url(
        r'^intrahospital_api/raw/patient/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalRawView.as_view(),
        name="raw_view"
    ),
    url(
        r'^intrahospital_api/cooked/patient/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalCookedView.as_view(),
        name="cooked_view"
    ),
]
