"""
Plugin definition for the ICU plugin
"""
from opal.core import plugins
from plugins.icu.urls import urlpatterns


class ICUPlugin(plugins.OpalPlugin):
    urls = urlpatterns
