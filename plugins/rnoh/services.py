"""
RNOH Service
"""
from opal.core import menus

from elcid.services import ClinicalService


class RNOHService(ClinicalService):

    @classmethod
    def visible_to(klass, user):
        return True


    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/rnoh/inpatients/',
            display='RNOH',
            icon='fa fa-hospital-o'
        )
