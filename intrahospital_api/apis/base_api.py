from django.conf import settings
from django.contrib.auth.models import User


class BaseApi(object):
    @property
    def user(self):
        return User.objects.get(username=settings.API_USER)
