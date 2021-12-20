"""
Plugin defnition for the handover plugin
"""
from opal.core import plugins

from plugins.ipc.urls import urlpatterns
from plugins.ipc import api


class IPCPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    apis = [
        (api.IsolatedBedApi.basename, api.IsolatedBedApi,),
    ]
    javascripts = {
        'opal.controllers': [
            "ipc/js/controllers/isolationHelper.js"
        ]
    }
