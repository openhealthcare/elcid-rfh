"""
Plugin definition for the admissions plugin
"""
from opal.core import plugins

from plugins.admissions import api


class AdmissionsPlugin(plugins.OpalPlugin):
    javascripts = {
        'opal.controllers': [
            'js/admissions/admission_view_controller.js'
        ]
    }

    apis = [
        ('admissions', api.AdmissionViewSet)
    ]
