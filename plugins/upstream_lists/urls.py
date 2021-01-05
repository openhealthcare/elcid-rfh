"""
Upstream list urls
"""
from django.urls import path

from plugins.upstream_lists import views

urlpatterns = [
    path(
        'templates/patient_list.html/upstream/<slug>',
        views.UpstreamListTemplateView.as_view(),
        name='upstream_list_template'
    )
]
