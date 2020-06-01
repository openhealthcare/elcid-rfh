"""
Plugin definition for the ICU plugin
"""
from opal.core import plugins, menus
from opal.models import UserProfile

from plugins.icu.constants import ICU_ROLE
from plugins.icu.urls import urlpatterns

class ICUPlugin(plugins.OpalPlugin):
    urls = urlpatterns

    @classmethod
    def get_menu_items(self, user):
        if not user:
            return []

        dashboard = menus.MenuItem(
            href='/#/ICU/',
            display='ICU',
            icon='fa fa-hospital-o',
            activepattern='/#/ICU/'
        )

        profile = UserProfile.objects.get(user=user)
        if profile.roles.filter(name=ICU_ROLE).exists():
            return [dashboard]

        if user.is_superuser:
            return [dashboard]

        return []
