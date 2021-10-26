"""
Covid service
"""
from opal.core import menus

from elcid.services import ClinicalService

from plugins.covid.constants import COVID_ROLE


class CovidService(ClinicalService):

    role_name = COVID_ROLE

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/covid-19/',
            display='COVID-19',
            icon='fa fa-dashboard',
            activepattern='/#/covid-19/'
        )
