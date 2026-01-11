"""
IPC Service
"""
from opal.core import menus

from elcid.services import ClinicalService

from plugins.ipc.constants import IPC_ROLE


class IPCService(ClinicalService):

    @classmethod
    def visible_to(klass, user):
        return True # The excluded roles are hardcoded in ElcidPostLoginCtrl

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/ipc/',
            display='IPC',
            icon='fa fa-warning',
            activepattern='ipc'
            )
