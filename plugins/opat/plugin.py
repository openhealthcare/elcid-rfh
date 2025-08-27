"""
Plugin definition for the OPAT Opal plugin
"""
from opal.core import plugins

from plugins.opat.urls import urlpatterns
from plugins.opat import api


class OPATPlugin(plugins.OpalPlugin):
    urls = urlpatterns
    javascripts = {
        'opal.controllers': [
            'opat/js/controllers/clean_record.js'
        ]
    }

    apis = [
        ('opat_test_summary', api.OPATTestSummaryAPI)
    ]
