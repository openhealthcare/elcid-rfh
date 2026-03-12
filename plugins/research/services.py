"""
Research plugin service definition
"""
from opal.core import menus

from elcid.services import ClinicalService


class ResearchService(ClinicalService):

    @classmethod
    def visible_to(klass, user):
        return False
        print('hai')
        if user.is_superuser:
            return True
        return False


    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/research/',
            display='Research',
            icon='fa fa-books'
        )
