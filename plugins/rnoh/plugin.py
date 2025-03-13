"""
Plugin definition for elcid.plugins.rhoh
"""
from opal.core import plugins

from plugins.rnoh.urls import urlpatterns


class RNOHPlugin(plugins.OpalPlugin):

    urls = urlpatterns
    javascripts = {
        'opal.controllers': [
            'js/controllers/rnoh_find_patient.js'
        ]
    }
