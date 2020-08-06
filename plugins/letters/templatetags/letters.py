"""
Custom templatetags for the Letters Module
"""
from django import template
from django.urls import reverse
from django.conf import settings

register = template.Library()


@register.inclusion_tag('letters/templatetags/pdf_link.html')
def pdf_link(*args, **kwargs):
    return {
        "url": reverse(*args, kwargs=kwargs),
        "settings": settings
    }
