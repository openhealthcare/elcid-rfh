"""
TB service
"""
from opal.core import menus
from opal.models import UserProfile

from elcid.services import ClinicalService

from plugins.tb.constants import TB_ROLE


class TBService(ClinicalService):

    role_name = TB_ROLE

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/tb/clinic-list',
            display='TB',
            icon='fa fa-columns',
            activepattern='/#/tb/clinic-list'
        )
