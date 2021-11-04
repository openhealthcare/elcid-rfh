"""
Plugin definition for the OPAT Opal plugin
"""
from opal.core import plugins
from plugins.opat.urls import urlpatterns


class OPATPlugin(plugins.OpalPlugin):
    urls = urlpatterns
    javascripts = {
        'opal.controllers': [
            'opat/js/controllers/clean_record.js'
        ]
    }
