"""
Plugin definition for the ICU plugin
"""
from opal.core import plugins, menus
from opal.models import UserProfile

from plugins.icu.urls import urlpatterns

class ICUPlugin(plugins.OpalPlugin):
    urls = urlpatterns
