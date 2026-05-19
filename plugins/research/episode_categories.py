"""
Custom Episode Category for the IPC Plugin
"""
from opal.core import episodes


class ResearchEpisode(episodes.EpisodeCategory):
    detail_template = 'detail/research.html'
    display_name    = 'Research'

    @classmethod
    def episode_visible_to(klass, episode, user):
        return True
