from django.conf import settings
from django.utils.module_loading import import_string


def get_lab_test_api():
    return import_string(settings.INTRAHOSPITAL_API)()
