"""
Plugin definition for the OPAT Opal plugin
"""
from opal.core import plugins


class OPATPlugin(plugins.OpalPlugin):
    javascripts = {
        'opal.controllers': [
            'opat/js/controllers/clean_record.js'
        ]
    }
