"""
Plugin definition for the Covid Opal plugin
"""
from opal.core import plugins

from plugins.covid.urls import urlpatterns

class CovidPlugin(plugins.OpalPlugin):
    urls = urlpatterns
