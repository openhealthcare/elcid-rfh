"""
Plugin definition for the appointments plugin
"""
from opal.core import plugins

from plugins.appointments import api


class AppointmentPlugin(plugins.OpalPlugin):
    javascripts = {
        'opal.controllers': [
            'js/appointments/appointment_view.controller.js'
        ]
    }

    apis = [
        ('appointments', api.AppointmentViewSet)
    ]
