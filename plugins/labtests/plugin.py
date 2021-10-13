"""
Plugin definition for the labtests Opal plugin
"""
from opal.core import plugins

from plugins.labtests.urls import urlpatterns
from plugins.labtests import api


class LabtestsPlugin(plugins.OpalPlugin):
    urls = urlpatterns
    javascripts = {}

    apis = [
        (api.LabTest.base_name, api.LabTest,),
    ]
