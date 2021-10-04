"""
Custom episode category for the RNOH plugin
"""
from opal.core import episodes


class RNOHEpisode(episodes.EpisodeCategory):
    detail_template = 'detail/rnoh.html'
    display_name    = 'RNOH'
