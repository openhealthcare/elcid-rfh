"""
Plugin definition for the TB Opal plugin
"""
from opal.core import plugins
from opal.core import menus
from opal.models import UserProfile
from plugins.tb.urls import urlpatterns
from plugins.tb import constants as tb_constants
from plugins.tb import api


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
            'js/tb/controllers/mantoux_test.js',
            'js/tb/controllers/add_episode_helper.js',
            'js/tb/directives.js'
            # 'js/tb/services/larry.js',
        ],
        'opal.services': [
            'js/tb/services/treatment_utils.js',
            'js/tb/services/treatment_record.js',
            'js/tb/services/test_summary_loader.js',
        ],
    }

    apis = [
        ('tb_test_summary', api.TbTestSummary,),
    ]


    @classmethod
    def get_menu_items(self, user):
        if not user:
            return []

        profile = UserProfile.objects.get(
            user=user
        )
        if profile.readonly:
            return []

        is_tb = profile.roles.filter(
            name=tb_constants.TB_ROLE
        ).exists()

        if is_tb:
            return [
                menus.MenuItem(
                    href='/pathway/#/add_tb_patient',
                    display='Add Patient',
                    icon='fa fa-plus',
                    activepattern='/pathway/#/add_tb_patient'
                )
            ]
        elif user.is_superuser:
            return [
                menus.MenuItem(
                    href='/pathway/#/add_tb_patient',
                    display='Add TB Patient',
                    icon='fa fa-plus',
                    activepattern='/pathway/#/add_tb_patient'
                )
            ]
        else:
            return []

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
