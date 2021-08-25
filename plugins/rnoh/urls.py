"""
RNOH urls
"""
from django.urls import path

from plugins.rnoh import views

urlpatterns = [
    path(
        'templates/rnoh/inpatients.html',
        views.RNOHInpatientsView.as_view(),
        name='rnoh_inpatients'
    ),
    path(
        'templates/rnoh/ward_list/<ward_name>/',
        views.RNOHWardListView.as_view(),
        name='rnoh_ward_list'
    ),
    path(
        'templates/rnoh/numbers.html',
        views.UsefulNumbersView.as_view(),
        name="rnoh_useful_numbers"
    )
]
