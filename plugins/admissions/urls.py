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
        'admissions/bedboard/hospitals/',
        views.BedboardHospitalListView.as_view(),
        name='admission_bedboard_hospital_list'
    ),
    path(
        'admissions/bedboard/hospital/<hospital_code>/',
        views.BedboardHospitalDetailView.as_view(),
        name='admission_bedboard_hospital_detail'
    ),
    path(
        'admissions/bedboard/ward/<ward_name>/',
        views.BedboardWardDetailView.as_view(),
        name='admission_bedboard_ward_detail'
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
        'templates/admissions/encounter/contacts/<encounter_id>/',
        views.LocationHistoryEncounterContactsView.as_view(),
        name='location_history_encounter_contacts'
    ),
    path(
        'templates/admissions/encounter/contacts/inpatients/<encounter_id>/',
        views.LocationHistoryEncounterRemainingInpatientContactsView.as_view(),
        name='location_history_remaining_inpatient_encounter_contacts'
    ),
    path(
        'templates/admissions/location-history/<location_code>/',
        views.LocationHistoryView.as_view(),
        name='location_history'
    )

]
