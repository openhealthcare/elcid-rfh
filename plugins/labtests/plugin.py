"""
Plugin definition for the labtests Opal plugin
"""
from opal.core import plugins

from plugins.labtests.urls import urlpatterns
from plugins.labtests import api


class LabtestsPlugin(plugins.OpalPlugin):
    urls = urlpatterns
    javascripts = {
        # Add your javascripts here!
        'opal.labtests': [
            # 'js/labtests/app.js',
            # 'js/labtests/controllers/larry.js',
            # 'js/labtests/services/larry.js',
        ]
    }

    apis = [
        (api.LabTest.base_name, api.LabTest,),
    ]
