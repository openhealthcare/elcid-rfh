from django import template

register = template.Library()


@register.inclusion_tag('templatetags/key_investigations.html')
def key_investigations(url_base, title=None, icon=None, body_class=None):
    return {
        "url_base": url_base,
        "title": title or 'Key Investigations',
        "body_class": body_class,
        "icon": icon or "fa fa-crosshairs"
    }
