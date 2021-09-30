"""
Templatetags for the IPC module
"""
from django import template

from plugins.admissions.models import UpstreamLocation

from plugins.ipc import constants
from plugins.ipc.episode_categories import IPCEpisode
from plugins.ipc.models import IPCStatus

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

    return {'alerts': alerts[:8]}


@register.inclusion_tag('templatetags/ipc_status.html')
def ipc_status(patient, **k):
    status = patient.ipcstatus_set.get()

    model_fields = set([i.name for i in IPCStatus._meta.get_fields() if '_date' in i.name])

    alerts = []

    for fname in model_fields:
        status_fname = fname.replace('_date', '')

        if getattr(status, status_fname):

            alerts.append([
                constants.ALERT_DISPLAY[status_fname],
                getattr(status, fname),
                constants.ADVICE[status_fname]
            ])

    return {'alerts': alerts}
