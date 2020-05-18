"""
Custom templatetags for the Covid Module
"""
from django import template
from opal.templatetags.forms import _model_and_field_from_path


register = template.Library()


@register.filter
def help(value):
    model, field = _model_and_field_from_path(value)
    return field.help_text
