"""
Panels for the elCID application
"""
from django import template
from opal.templatetags.panels import record_panel

register = template.Library()

@register.inclusion_tag('templatetags/wide_panel.html', takes_context=True)
def wide_panel(context, *args, **kwargs):
    return record_panel(context, *args, **kwargs)
