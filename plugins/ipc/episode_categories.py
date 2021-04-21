"""
Custom episode category for the IPC plugin
"""
from opal.core import episodes


class IPCEpisode(episodes.EpisodeCategory):
    detail_template = 'detail/ipc.html'
    display_name    = 'IPC'
