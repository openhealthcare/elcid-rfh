"""
Templatetags for the IPC module
"""
from django import template

from plugins.admissions.models import UpstreamLocation

from plugins.ipc.episode_categories import IPCEpisode

register = template.Library()

@register.inclusion_tag('templatetags/ward_count.html')
def ward_count(ward_name, **kwargs):
    return {
        'count': UpstreamLocation.objects.filter(ward=ward_name).count()
    }

@register.inclusion_tag('templatetags/location_alerts.html')
def location_alerts(location, **k):
    alerts = []
    ipc_episodes = location.patient.episode_set.filter(
        category_name=IPCEpisode.display_name)

    if ipc_episodes.exists():
        alerts = ipc_episodes.first().infectionalert_set.all()

    return {'alerts': alerts}
