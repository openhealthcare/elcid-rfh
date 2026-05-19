"""
Plugin definition for elcid.plugins.research
"""
from opal.core import plugins

from plugins.research import api
from plugins.research.urls import urlpatterns


class ResearchPlugin(plugins.OpalPlugin):

    urls = urlpatterns

    javascripts = {
        'opal.controllers': [
            'js/controllers/add_study.js',
            'js/controllers/delete_study.js',
            'js/controllers/close_study.js',
            'js/controllers/add_study_participant.js',
            'js/controllers/remove_participant.js',
            'js/controllers/new_research_note.js'
        ]
    }

    apis = [
        (api.StudyViewSet.basename, api.StudyViewSet),
        (api.StudySearchMRNsViewSet.basename, api.StudySearchMRNsViewSet),
        (api.StudyAddParticipantsViewSet.basename, api.StudyAddParticipantsViewSet),
        (api.StudyRemoveParticipantsViewSet.basename, api.StudyRemoveParticipantsViewSet),
        (api.StudyCloseViewSet.basename, api.StudyCloseViewSet),
        (api.ResearchNoteViewSet.basename, api.ResearchNoteViewSet),
    ]
