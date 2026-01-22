"""
Research Study specific urls
"""
from django.urls import path

from plugins.research import views

urlpatterns = [
    path(
        'templates/research/home.html',
        views.ResearchHomeView.as_view(),
        name='research_home'
    ),
    path(
        'templates/research/study_list.html/',
        views.StudyListView.as_view(),
        name='research_study_list'
    ),

    path(
        'templates/research/study_detail.html',
        views.StudyDetailView.as_view(),
        name='research_study_detail'
    ),
    path(
        'templates/research/study_add_participants.html/',
        views.StudyAddParticipantsView.as_view(),
        name='research_study_list'
    ),
    path(
        'templates/research/study_participant_list.html/',
        views.StudyParticipantListView.as_view(),
        name='research_study_participant_list'
    ),
    path(
        'research/study/<study_id>/download-data/',
        views.StudyDownloadView.as_view(),
        name='research_study_download_data'
    ),
]
