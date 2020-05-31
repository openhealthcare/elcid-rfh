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
            'js/covid/covid_test_summary.controller.js'
        ]
    }

    @classmethod
    def get_menu_items(self, user):
        if not user:
            return []

        dashboard = menus.MenuItem(
            href='/#/covid-19/',
            display='COVID-19',
            icon='fa fa-dashboard',
            activepattern='/#/covid-19/'
        )

        profile = UserProfile.objects.get(user=user)
        if profile.roles.filter(name=COVID_ROLE).exists():
            return [dashboard]

        if user.is_superuser:
            return [dashboard]

        return []

    apis = [
        ('covid_service_test_summary', api.CovidServiceTestSummaryAPI)
    ]
