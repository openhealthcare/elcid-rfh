"""
ICU Service
"""
from opal.core import menus

from elcid.services import ClinicalService

from plugins.icu.constants import ICU_ROLE


class ICUService(ClinicalService):

    role_name = ICU_ROLE

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/ICU/',
            display='ICU',
            icon='fa fa-hospital-o',
            activepattern='/#/ICU/'
        )
