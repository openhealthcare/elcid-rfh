"""
Plugin definition for the TB Opal plugin
"""
from opal.core import plugins
from opal.core import menus
from apps.tb.urls import urlpatterns


class AddTBPatient(menus.MenuItem):
    def for_user(self, user):
        return user and user.is_superuser


class TbPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our Opal application.
    """
    urls = urlpatterns
    javascripts = {
        # Add your javascripts here!
        'opal.controllers': [
            # 'js/tb/app.js',
            'js/tb/filters.js',
            'js/tb/controllers/tb_symptom_complex.js',
            'js/tb/controllers/patient_consultation.js',
            'js/tb/controllers/new_subrecord_step.js',
            'js/tb/controllers/tb_diagnosis.js',
            'js/tb/controllers/tb_treatment.js',
            'js/tb/controllers/mantoux_test.js'
            # 'js/tb/services/larry.js',
        ],
        'opal.services': [
            'js/tb/services/treatment_utils.js',
            'js/tb/services/treatment_record.js',
        ],
    }
    menuitems = [
        AddTBPatient(
            href='/pathway/#/add_tb_patient',
            display='Add Patient',
            icon='fa fa-plus',
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
