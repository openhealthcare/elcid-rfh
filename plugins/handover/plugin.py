"""
Plugin definition for the handover plugin
"""
from opal.core import plugins

from plugins.handover import api


class HandoverPlugin(plugins.OpalPlugin):
    apis = [
        ('amthandovers', api.AMTHandoverViewSet),
    ]
