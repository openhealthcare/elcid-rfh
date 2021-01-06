"""
Plugin definition for upstream lists plugin
"""
from opal.core import plugins

from plugins.upstream_lists import api
from plugins.upstream_lists.urls import urlpatterns

class UpstreamListPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    apis = [
        (api.UpstreamPatientListViewSet.base_name, api.UpstreamPatientListViewSet)
    ]
