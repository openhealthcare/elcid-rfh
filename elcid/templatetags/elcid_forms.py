from django import template
from opal.templatetags.forms import _radio
register = template.Library()


@register.inclusion_tag('_helpers/radio_columns.html')
def radio_columns(*args, **kwargs):
    return _radio(*args, **kwargs)

