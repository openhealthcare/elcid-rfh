"""
Plugin definition for the labtests Opal plugin
"""
from opal.core import plugins

from plugins.labtests.urls import urlpatterns
from plugins.labtests import api


class LabtestsPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    javascripts = {
        'opal.controllers': [
            'labtests/js/controllers/lab_detail.js',
        ],
        'opal.services': [
            'labtests/js/services/lab_detail_loader.js',
            "labtests/js/services/star_observation.js"
        ]
    }

    apis = [
        (api.StarObservation.base_name, api.StarObservation,),
        (api.LabTest.base_name, api.LabTest,),
    ]

    def list_schemas(self):
        """
        Return any patient list schemas that our plugin may define.
        """
        return {}

    def roles(self, user):
        """
        Given a (Django) USER object, return any extra roles defined
        by our plugin.
        """
        return {}
