"""
RNOH Service
"""
from opal.core import menus

from elcid.services import ClinicalService


class RNOHService(ClinicalService):

    role_name = 'RNOH' # TODO: Generate role

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/rnoh/inpatients/',
            display='RNOH',
            icon='fa fa-hospital-o'
        )
