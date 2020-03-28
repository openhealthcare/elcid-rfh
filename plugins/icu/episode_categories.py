"""
Custom Episode Category for ICU plugin
"""
from opal.core import episodes


class ICUHandoverEpisode(episodes.EpisodeCategory):
    display_name    = "ICU Handover"
    detail_template = "detail/icu_handover.html"
