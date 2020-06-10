"""
Plugin definition for the dischargesummary plugin
"""
from opal.core import plugins

from plugins.admissions import api


class AdmissionsPlugin(plugins.OpalPlugin):
    javascripts = {
        'opal.controllers': [
#            'js/dischargesummary/dischargesummary_view_controller.js'
        ]
    }

    apis = [
        ('dischargesumamries', api.DischargeSummaryViewSet)
    ]
