"""
Custom episode category for the RNOH plugin
"""
from opal.core import episodes


class RNOHEpisode(episodes.EpisodeCategory):
    detail_template = 'detail/rnoh.html'
    display_name    = 'RNOH'

    def get_advice(self):
        """
        Ordering for RNOH is unlike anything else
        """
        return self.episode.microbiologyinput_set.all().order_by('when')
