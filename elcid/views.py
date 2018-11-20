"""
eLCID specific views.
"""
from django.http import HttpResponse
from django.views.generic import View

from opal.core import application

app = application.get_app()


class Error500View(View):
    """
    Demonstrative 500 error to preview templates.
    """
    def get(self, *args, **kwargs):
        if self.request.META['HTTP_USER_AGENT'].find('Googlebot') != -1:
            return HttpResponse('No')
        raise Exception("This is a deliberate error")
