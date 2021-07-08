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
    path(
        'templates/admissions/transfer_history/<spell_number>/',
        views.SpellLocationHistoryView.as_view(),
        name='spell_location_history'
    ),
    path(
        'templates/admissions/slice_contacts/<slice_id>/',
        views.SliceContactsView.as_view(),
        name='slice_contacts'
    ),
    path(
        'templates/admissions/location-history/<location_code>/',
        views.LocationHistoryView.as_view(),
        name='location_history'
    )


]
