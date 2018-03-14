"""
Plugin definition for the TB Opal plugin
"""
from opal.core import plugins
from opal.core import menus
from apps.tb.urls import urlpatterns


class TbPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our Opal application.
    """
    urls = urlpatterns
    javascripts = {
        # Add your javascripts here!
        'opal.controllers': [
            # 'js/tb/app.js',
            'js/tb/controllers/tb_symptom_complex.js',
            'js/tb/controllers/patient_consultation.js',
            'js/tb/controllers/new_subrecord_step.js',
            # 'js/tb/services/larry.js',
        ]
    }
    menuitems = [
        menus.MenuItem(
            href='/pathway/#/add_tb_patient',
            display='Add TB Patient',
            icon='fa fa-coffee',
            activepattern='/pathway/#/add_tb_patient'
        )
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
