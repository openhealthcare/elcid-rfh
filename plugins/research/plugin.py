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

        ]
    }

    apis = [
        (api.StudyViewSet.basename, api.StudyViewSet)
    ]
