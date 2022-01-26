"""
Plugin definition for the epma Opal plugin
"""
from opal.core import plugins

from plugins.epma import api


class EPMAPlugin(plugins.OpalPlugin):
    javascripts = {
        'opal.controllers': [
            'js/epma/controllers/epma_detail.js',
        ]
    }

    apis = [
        (api.EPMAMedOrder.basename, api.EPMAMedOrder,),
    ]
