"""
Plugin definition for the labtests Opal plugin
"""
from opal.core import plugins

from plugins.add_patients.urls import urlpatterns


class AddPatientsPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our Opal application.
    """
    urls = urlpatterns
    javascripts = {
        'opal.controllers': [
            'js/add_patients/add_patients.js',
            'js/add_patients/directives.js'
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