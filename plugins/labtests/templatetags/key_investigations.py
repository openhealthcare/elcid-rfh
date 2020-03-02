from django import template

register = template.Library()


@register.inclusion_tag('templatetags/key_investigations.html')
def key_investigations(url_base):
    return {"url_base": url_base}
