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
            'js/tb/controllers/add_remove_tag_modal.js',
            'js/tb/controllers/patient_consultation.js',
            'js/tb/controllers/new_subrecord_step.js',
            'js/tb/controllers/tb_diagnosis.js',
            'js/tb/controllers/tb_treatment.js',
            'js/tb/controllers/mantoux_test.js',
            'js/tb/controllers/add_episode_helper.js',
            'js/tb/controllers/tb_date_helper.js',
            'js/tb/controllers/tb_mdt_no_action.js',
            # 'js/tb/services/larry.js',
        ],
        'opal.services': [
            'js/tb/services/treatment_utils.js',
            'js/tb/services/treatment_record.js',
        ],
    }

    apis = [
        ('tb_test_summary', api.TbTestSummary,),
        (api.TbTests.basename, api.TbTests,),
        (api.TBAppointments.basename, api.TBAppointments,),
        (api.TBMDTNoAction.basename, api.TBMDTNoAction),
    ]
