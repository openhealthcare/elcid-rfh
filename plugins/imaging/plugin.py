"""
Plugin definition for the imaging plugin
"""
from opal.core import plugins

from plugins.imaging import api


class AdmissionsPlugin(plugins.OpalPlugin):
    javascripts = {
        'opal.controllers': [
            'js/imaging/imaging_view_controller.js'
        ]
    }

    apis = [
        ('imaging', api.ImagingViewSet)
    ]
