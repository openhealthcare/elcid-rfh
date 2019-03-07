"""
Plugin definition for the letters Opal plugin
"""
from opal.core import plugins

from plugins.letters.urls import urlpatterns

class LettersPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our Opal application.
    """
    urls = urlpatterns
    javascripts = {
        # Add your javascripts here!
        'opal.letters': [
            'js/letters/app.js',
            'js/letters/controllers/blank_controller.js',
        ]
    }

    stylesheets = [
        "css/letters.css"
    ]

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