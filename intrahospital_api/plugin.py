"""
Plugin definition for the pathway Opal plugin
"""
from opal.core import plugins
from intrahospital_api.urls import urlpatterns
from intrahospital_api import api


class IntraHospitalApiPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our OPAL application.
    """
    urls = urlpatterns

    javascripts = {
        'opal.controllers': [
            'js/intrahospital_api/controllers/reconcile_patient.js'
        ],
        'opal.services': [
            'js/intrahospital_api/services/initial_patient_lab_load_status.js'
        ]
    }
    apis = [
        ("patient", api.PatientViewSet,),
        ("upstream", api.UpstreamDataViewset,)
    ]
