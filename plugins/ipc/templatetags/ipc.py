"""
Templatetags for the IPC module
"""
from django import template

from plugins.admissions.models import UpstreamLocation

from plugins.ipc import constants, models
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


@register.inclusion_tag('templatetags/ipc_check_box_and_date_field.html')
def ipc_check_box_and_date_field(field):
    ctx = {"formname": "form", "field": field}
    ctx["date_field"] = f"{field}_date"
    ctx["label"] = models.IPCStatus._get_field_title(field)
    ctx["model"] = f"editing.ipc_status.{field}"
    ctx["date_model"] = f"{ctx['model']}_date"
    if not models.IPCStatus._meta.get_field(ctx["date_field"]):
        raise ValueError(f'Unknown IPC date field {ctx["date_field"]}')
    return ctx
