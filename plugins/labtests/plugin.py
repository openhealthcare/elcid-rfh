"""
Plugin definition for the labtests Opal plugin
"""
from opal.core import plugins

from plugins.labtests.urls import urlpatterns

class LabtestsPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our Opal application.
    """
    urls = urlpatterns
    javascripts = {
        # Add your javascripts here!
        'opal.labtests': [
            # 'js/labtests/app.js',
            # 'js/labtests/controllers/larry.js',
            # 'js/labtests/services/larry.js',
        ]
    }

    def list_schemas(self):
        """
        Return any patient list schemas that our plugin may define.
        """
        return {}

    def roles(self, user):
        """
        Given a (Django) USER object, return any extra roles defined
        by our plugin.
        """
        return {}