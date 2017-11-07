from django.conf import settings
from django.utils.module_loading import import_string


def get_api():
    return import_string(settings.INTRAHOSPTIAL_API)
