"""
TB service
"""
from opal.core import menus
from opal.models import UserProfile

from elcid.services import ClinicalService

from plugins.tb.constants import TB_ROLE


class TBService(ClinicalService):

    @classmethod
    def visible_to(klass, user):
        return True # The excluded roles are hardcoded in ElcidPostLoginCtrl

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/tb/clinic-list',
            display='TB',
            icon='fa fa-columns',
            activepattern='/#/tb/clinic-list'
        )
