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
            'js/letters/controllers/redirect_controller.js',
        ]
    }

    stylesheets = [
        "css/letters.css"
    ]
