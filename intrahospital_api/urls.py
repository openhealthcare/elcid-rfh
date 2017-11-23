"""
Urls for the intrahospital_api plugin
"""
from django.conf.urls import patterns, url

from intrahospital_api import views

urlpatterns = patterns(
    '',
    url(
        r'^intrahospital_api/raw/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalRawView.as_view(),
        name="raw_view"
    ),
    url(
        r'^intrahospital_api/cooked/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalCookedView.as_view(),
        name="cooked_view"
    ),

)
