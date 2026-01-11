"""
ICU Service
"""
from opal.core import menus

from elcid.services import ClinicalService

from plugins.icu.constants import ICU_ROLE


class ICUService(ClinicalService):

    @classmethod
    def visible_to(klass, user):
        return True # The excluded roles are hardcoded in ElcidPostLoginCtrl

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/ICU/',
            display='ICU',
            icon='fa fa-hospital-o',
            activepattern='/#/ICU/'
        )
