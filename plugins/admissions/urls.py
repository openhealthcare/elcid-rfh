"""
Admission specific urls
"""
from django.urls import path

from plugins.admissions import views

urlpatterns = [
    path(
        'templates/admissions/upstream_location/<pk>/',
        views.UpstreamLocationSnippet.as_view(),
        name='admission_upstream_snippet'
    ),

]
