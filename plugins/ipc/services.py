"""
IPC Service
"""
from opal.core import menus

from elcid.services import ClinicalService

from plugins.ipc.constants import IPC_ROLE


class IPCService(ClinicalService):

    role_name = IPC_ROLE

    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/ipc/',
            display='IPC',
            icon='fa fa-warning',
            activepattern='ipc'
            )
