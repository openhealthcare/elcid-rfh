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
    )
]
