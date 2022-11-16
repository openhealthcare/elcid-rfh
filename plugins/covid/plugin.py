"""
Plugin definition for the Covid Opal plugin
"""
from opal.core import plugins, menus
from opal.models import UserProfile

from plugins.covid import api
from plugins.covid.constants import COVID_ROLE
from plugins.covid.urls import urlpatterns


class CovidPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    javascripts = {
        'opal.controllers': [
            'js/covid/covid_test_summary.controller.js',
            'js/covid/send_covid_to_epr.controller.js',
            'js/covid/covid_letter_helper.controller.js',
        ]
    }

    apis = [
        ('covid_service_test_summary', api.CovidServiceTestSummaryAPI),
        ('covid_cxr', api.CovidCXRViewSet),
        (api.SendCovidFollowUpCallUpstream.basename, api.SendCovidFollowUpCallUpstream),
        (
            api.SendCovidFollowUpCallFollowUpCall.basename,
            api.SendCovidFollowUpCallFollowUpCall
        ),
        (api.SendCovidSixMonthFollowUp.basename, api.SendCovidSixMonthFollowUp),
    ]
