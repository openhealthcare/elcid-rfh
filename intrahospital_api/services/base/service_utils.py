from django.conf import settings
from django.contrib.auth.models import User
from django.utils import module_loading


def get_backend(service):
    api_state = settings.UPSTREAM_BACKEND_STATE
    backend_str = "intrahospital_api.services.{}.{}_backend.Backend".format(
        service, api_state
    )
    api = module_loading.import_string(backend_str)
    return api()


def get_user():
    return User.objects.get(username=settings.API_USER)
