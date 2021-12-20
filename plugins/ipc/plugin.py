"""
Plugin defnition for the handover plugin
"""
from opal.core import plugins

from plugins.ipc.urls import urlpatterns
from plugins.ipc import api


class IPCPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    apis = [
        (api.BedStatusApi.basename, api.BedStatusApi),
    ]

    javascripts = {
        "opal.controllers": [
            'ipc/js/controllers/bed_status.js'
        ]
    }
