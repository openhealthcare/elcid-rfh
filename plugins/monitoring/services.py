"""
Monitoring plugin service definition
"""
from opal.core import menus

from elcid.services import ClinicalService

class MetricsService(ClinicalService):

    @classmethod
    def visible_to(klass, user):
        return True

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/metrics/',
            display='Metrics',
            icon='fa fa-bar-chart'
        )
