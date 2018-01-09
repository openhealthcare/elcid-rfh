"""
Plugin definition for the TB Opal plugin
"""
from opal.core import plugins

from apps.tb.urls import urlpatterns


class TbPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our Opal application.
    """
    urls = urlpatterns
    javascripts = {
        # Add your javascripts here!
        'opal.tb': [
            # 'js/tb/app.js',
            # 'js/tb/controllers/larry.js',
            # 'js/tb/services/larry.js',
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
