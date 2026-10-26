"""
Panels for the elCID application
"""
from django import template
from django.utils.safestring import mark_safe

from opal.templatetags.panels import record_panel

register = template.Library()

@register.inclusion_tag('templatetags/wide_panel.html', takes_context=True)
def wide_panel(context, *args, **kwargs):
    return record_panel(context, *args, **kwargs)

@register.filter()
def nbspjust(value, length):
    diff = int(length) - len(value)
    if diff <= 0:
        return value

    return mark_safe("<span style='font-family: monospace'>" + value + '&nbsp;' * diff + "</span>")
