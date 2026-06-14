"""
Research plugin service definition
"""
from opal.core import menus

from elcid.services import ClinicalService

from plugins.research.models import Study


class ResearchService(ClinicalService):

    @classmethod
    def visible_to(klass, user):
        if user.is_superuser:
            return True
        if Study.objects.filter(users=user).count() > 0:
            return True
        return False


    @classmethod
    def as_menuitem(klass):
        return menus.MenuItem(
            href='/#/research/',
            display='Research',
            icon='fa fa-books'
        )
