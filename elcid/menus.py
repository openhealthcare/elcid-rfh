"""
Custom menu item for elCID services
"""
from opal.core import menus

from elcid.services import ClinicalService


class ServicesMenuItem(menus.MenuItem):

    def __init__(self, *a, **k):
        self.user = k['user']
        del k['user']

        super().__init__(*a, **k)

        if not self.template_name:
            self.template_name = 'partials/services_menu_item.html'

        services = [cs.as_menuitem() for cs in ClinicalService.for_user(self.user)]
        self.services = sorted(services, key=lambda x: x.display)

    def __iter__(self):
        return (i for i in self.services)
