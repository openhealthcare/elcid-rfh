"""
Custom episode category for the IPC plugin
"""
from opal.core import episodes

from plugins.ipc.constants import IPC_ROLE


class IPCEpisode(episodes.EpisodeCategory):
    detail_template = 'detail/ipc.html'
    display_name    = 'IPC'

    @classmethod
    def episode_visible_to(klass, episode, user):
        from opal.models import UserProfile  # Avoid circular import

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.roles.filter(name=IPC_ROLE).exists():
            return True

        return False
