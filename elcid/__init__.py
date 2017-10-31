"""
elCID Royal Free Hospital implementation
"""

from opal.core import application
from opal.core import menus


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
        'js/elcid/controllers/procedure_form.js',
        'js/elcid/controllers/clinical_advice_form.js',
        'js/elcid/controllers/result_view.js',
        'js/elcid/controllers/rfh_find_patient.js',
        'js/elcid/controllers/bloodculture_pathway_form.js',
        'js/elcid/controllers/remove_patient_step.js',
        'js/elcid/controllers/tagging_step.js',
        'js/elcid/controllers/investigations.js',
        # used in the blood culture forms
        'js/elcid/services/blood_culture_helper.js',

        'js/elcid/services/blood_culture_record.js',

        # used to load in the blood cultures
        'js/elcid/services/blood_culture_loader.js',
        'js/elcid/services/episode_added_comparator.js',
    ]

    styles = [
        "css/elcid.css"
    ]

    patient_view_forms = {
        "General Consultation": "inline_forms/clinical_advice.html",
    }

    add_patient_menu_item = menus.MenuItem(
        href='/pathway/#/add_patient',
        display='Add Patient',
        icon='fa fa-plus',
        activepattern='/pathway/#/add_patient'
    )

    @classmethod
    def get_menu_items(klass, user=None):
        items = application.OpalApplication.get_menu_items(user=user)
        return items + [klass.add_patient_menu_item]
