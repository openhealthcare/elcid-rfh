"""
Custom episode category for the Covid plugin
"""
from opal.core import episodes


class CovidEpisode(episodes.EpisodeCategory):
    detail_template = 'detail/covid.html'
    display_name    = 'COVID-19'
