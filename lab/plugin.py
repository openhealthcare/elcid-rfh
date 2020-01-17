"""
Plugin definition for the lab OPAL plugin
"""
from opal.core import plugins


class LabPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our OPAL application.
    """
    urls = []
