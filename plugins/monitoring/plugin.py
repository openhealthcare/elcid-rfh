"""
Plugin definition for the monitoring plugin
"""
from opal.core import plugins

from plugins.monitoring.urls import urlpatterns

class MonitoringPlugin(plugins.OpalPlugin):

    urls = urlpatterns

    javascripts = {
        'opal.services': [
            'js/monitoring/render_graph.js'
        ]
    }
