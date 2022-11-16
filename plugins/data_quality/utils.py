from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_email(title, template_name, context):
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    send_mail(
        title,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMINS,
        html_message=html_message,
    )
