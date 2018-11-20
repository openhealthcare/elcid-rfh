from django.conf import settings
from django.contrib.auth.models import User
from django.utils import module_loading


def get_api(service):
    api_state = settings.API_STATE
    backend_str = "intrahospital_api.services.{}.backends.{}.Api".format(
        service, api_state
    )
    api = module_loading.import_string(backend_str)
    return api()


def get_user():
    return User.objects.get(username=settings.API_USER)
