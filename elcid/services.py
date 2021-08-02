"""
Defines a service discoverable for the elCID application
"""
from opal.core import discoverable


class ClinicalService(discoverable.DiscoverableFeature, discoverable.RestrictableFeature):
    module_name = 'services'

    @classmethod
    def visible_to(klass, user):

        if user.is_superuser:
            return True

        profile = UserProfile.objects.get(user=user)

        if profile.roles.filter(name=klass.role_name).exists():
            return True

        return False
