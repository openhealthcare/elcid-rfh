"""
elCID Royal Free Hospital implementation
"""

from opal.core import application
from opal.core import menus
from apps.tb import constants as tb_constants
from elcid import episode_categories


class StandardAddPatientMenuItem(menus.MenuItem):
    def for_user(self, user):
        from opal.models import UserProfile
        if user and user.is_superuser:
            return True
        return not UserProfile.objects.filter(
            user=user,
            roles__name=tb_constants.TB_ROLE
        ).exists()


# ie, not the TB one
standard_add_patient_menu_item = StandardAddPatientMenuItem(
    href='/pathway/#/add_patient',
    display='Add Patient',
    icon='fa fa-plus',
    activepattern='/pathway/#/add_patient'
)


class Application(application.OpalApplication):
    schema_module = 'elcid.schema'
    javascripts = [
        'js/elcid/routes.js',
        'js/elcid/filters.js',
        'js/elcid/directives.js',
        'js/elcid/controllers/discharge.js',
        'js/elcid/services/records/microbiology_input.js',
        'js/elcid/controllers/clinical_advice_form.js',
        'js/elcid/controllers/welcome.js',
        'js/elcid/controllers/clinical_advice_form.js',
        'js/elcid/controllers/lab_test_json_dump_view.js',
        'js/elcid/controllers/result_view.js',
        'js/elcid/controllers/rfh_find_patient.js',
        'js/elcid/controllers/bloodculture_pathway_form.js',
        'js/elcid/controllers/remove_patient_step.js',

        'js/elcid/services/demographics_search.js',


        'js/elcid/controllers/tagging_step.js',
        'js/elcid/controllers/investigations.js',
        # used in the blood culture forms
        'js/elcid/services/blood_culture_helper.js',

        'js/elcid/services/blood_culture_loader.js',
        'js/elcid/services/upstream_blood_culture_loader.js',
        'js/elcid/services/blood_culture_record.js',
        'js/elcid/services/lab_test_results.js',
        'js/elcid/services/demographics_search.js',
        'js/elcid/services/lab_test_summary_loader.js',
        'js/elcid/services/lab_test_json_dump.js',
        'js/elcid/services/observation_detail.js',
        'js/elcid/services/episode_added_comparator.js',
    ]

    styles = [
        "css/elcid.css"
    ]

    patient_view_forms = {
        "General Consultation": "inline_forms/clinical_advice.html",
    }

    default_episode_category = episode_categories.InfectionService.display_name

    @classmethod
    def get_menu_items(cls, user):
        menu_items = super(Application, cls).get_menu_items(user)
        if standard_add_patient_menu_item.for_user(user):
            menu_items.append(standard_add_patient_menu_item)
        else:
            menu_items = [i for i in menu_items if not i.href == "/"]

        return menu_items
