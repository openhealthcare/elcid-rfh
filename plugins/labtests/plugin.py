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
            'labtests/js/controllers/lab_detail_modal.js',
        ],
        'opal.services': [
            'labtests/js/services/lab_detail_loader.js',
        ]
    }

    apis = [
        (api.LabTest.basename, api.LabTest,),
    ]
