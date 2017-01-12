"""
elCID Royal Free Hospital implementation
"""

from opal.core import application


class Application(application.OpalApplication):
    schema_module = 'elcid.schema'
    javascripts = [
        'js/elcid/routes.js',
        'js/elcid/controllers/discharge.js',
        'js/elcid/services/records/microbiology_input.js',
        'js/elcid/controllers/clinical_advice_form.js',
        'js/elcid/controllers/welcome.js',
        'js/elcid/controllers/procedure_form.js',
        'js/elcid/controllers/clinical_advice_form.js',
        'js/elcid/controllers/result_view.js',
        'js/elcid/controllers/bloodculture_modal_form.js',
        'js/elcid/controllers/bloodculture_pathway_form.js',
        'js/elcid/services/blood_culture_form_helper.js',
        'js/elcid/services/blood_culture_helper.js',
        'js/elcid/services/dicharge_patient.js',
        'js/elcid/services/blood_culture_record.js',
        'js/elcid/services/flow.js',
    ]

    styles = [
        "css/elcid.css"
    ]

    patient_view_forms = {
        "General Consultation": "inline_forms/clinical_advice.html",
    }

    menuitems = [
        dict(
            href='/pathway/#/add_patient', display='Add Patient', icon='fa fa-plus',
            activepattern='/pathway/#/add_patient'),
    ]
