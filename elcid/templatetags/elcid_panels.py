"""
Panels for the elCID application
"""
from django import template
from opal.templatetags.panels import record_panel

register = template.Library()

@register.inclusion_tag('templatetags/wide_panel.html', takes_context=True)
def wide_panel(context, *args, **kwargs):
    return record_panel(context, *args, **kwargs)


@register.simple_tag(takes_context=True)
def query_string(context, replace=True, **kwargs):
    """
    Updates the current querydict with the required field

    By default it replaces the key

    It ignores the cacheBust key
    e.g.
    if we were at /?hello=there&good_bye=old_friend
    we could do
    /?{% query_string good_bye='viajo_amigo' %}
    and the template would render
    /?hello=there&good_bye=viajo_amigo
    """
    query_dict = context["request"].GET.copy()
    if "cacheBust" in query_dict:
        query_dict.pop("cacheBust")
    if replace:
        for k in kwargs.keys():
            if k in query_dict:
                query_dict.pop(k)
    query_dict.update(kwargs)
    return query_dict.urlencode()
