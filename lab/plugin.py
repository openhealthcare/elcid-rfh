"""
Plugin definition for the lab OPAL plugin
"""
from opal.core import plugins
from lab.urls import urlpatterns
from lab import api

class LabPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our OPAL application.
    """
    urls = urlpatterns

    apis = [
        ('infection_test_summary', api.InfectionTestSummary,),
    ]