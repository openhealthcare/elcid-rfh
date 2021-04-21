"""
Plugin definition for the admissions plugin
"""
from opal.core import plugins

from plugins.admissions import api
from plugins.admissions.urls import urlpatterns

class AdmissionsPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    javascripts = {
        'opal.controllers': [
            'js/admissions/admission_view_controller.js'
        ]
    }

    apis = [
        ('admissions', api.AdmissionViewSet)
    ]
