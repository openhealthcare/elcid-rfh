"""
Urls for the intrahospital_api plugin
"""
from django.conf.urls import url

from intrahospital_api import views

urlpatterns = [
    url(
        r'^intrahospital_api/raw/lab_tests/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalRawLabTestView.as_view(),
        name="raw_lab_tests"
    ),
    url(
        r'^intrahospital_api/cooked/lab_tests/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalCookedLabTestView.as_view(),
        name="cooked_lab_tests"
    ),
    url(
        r'^intrahospital_api/cooked/results/(?P<hospital_number>[0-9A-Za-z_\-]+)/json$',
        views.results_as_json,
        name="cooked_lab_test_json_view"
    ),
    url(
        r'^intrahospital_api/raw/appointments/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalRawAppointmentsView.as_view(),
        name="raw_appointments"
    ),
    url(
        r'^intrahospital_api/cooked/appointments/(?P<hospital_number>[0-9A-Za-z_\-]+)$',
        views.IntrahospitalCookedAppointmentsView.as_view(),
        name="cooked_appointments"
    )
]
