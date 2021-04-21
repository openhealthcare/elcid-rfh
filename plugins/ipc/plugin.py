"""
Plugin defnition for the handover plugin
"""
from opal.core import plugins

from plugins.ipc.urls import urlpatterns

class IPCPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    apis = []
