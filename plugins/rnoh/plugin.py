"""
Plugin definition for elcid.plugins.rhoh
"""
from opal.core import plugins

from plugins.rnoh.urls import urlpatterns


class RNOHPlugin(plugins.OpalPlugin):

    urls = urlpatterns
