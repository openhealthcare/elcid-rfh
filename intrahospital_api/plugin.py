"""
Plugin definition for the pathway Opal plugin
"""
from opal.core import plugins
from intrahospital_api.urls import urlpatterns


class IntraHospitalApiPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our OPAL application.
    """
    urls = urlpatterns
