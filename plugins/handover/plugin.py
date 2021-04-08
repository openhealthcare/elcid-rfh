"""
Plugin definition for the handover plugin
"""
from opal.core import plugins

from plugins.handover import api
from plugins.handover.urls import urlpatterns


class HandoverPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    apis = [
        ('amthandovers',     api.AMTHandoverViewSet),
        ('nursinghandovers', api.NursingHandoverViewSet),
    ]
