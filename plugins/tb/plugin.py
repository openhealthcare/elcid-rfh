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
            'js/tb/controllers/tb_date_helper.js',
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
        (api.TbTests.base_name, api.TbTests,),
        (api.TBAppointments.base_name, api.TBAppointments,),
    ]

    @classmethod
    def get_menu_items(self, user):
        if not user or not user.is_authenticated:
            return []

        if not UserProfile.objects.filter(
            user=user,
            roles__name=tb_constants.TB_ROLE
        ).exists:
            return []

        return [
            menus.MenuItem(
                href='/#/tb/clinic-list',
                display='TB',
                icon='fa fa-columns',
                activepattern='/#/tb/clinic-list'
            )
        ]
