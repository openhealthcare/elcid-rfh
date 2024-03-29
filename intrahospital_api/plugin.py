"""
Plugin definition for the pathway Opal plugin
"""
from opal.core import plugins
from intrahospital_api import api


class IntraHospitalApiPlugin(plugins.OpalPlugin):
    """
    Main entrypoint to expose this plugin to our OPAL application.
    """

    javascripts = {
        'opal.controllers': [
            'js/intrahospital_api/controllers/reconcile_patient.js'
        ],
    }
    apis = [
        ("patient", api.PatientViewSet,),
        ("upstream", api.UpstreamDataViewset,)
    ]
