"""
eLCID specific views.
"""
import csv
import random

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.generic import TemplateView, FormView, View

from opal.core import application

from elcid.forms import BulkCreateUsersForm

app = application.get_app()


class Error500View(View):
    """
    Demonstrative 500 error to preview templates.
    """
    def get(self, *args, **kwargs):
        if self.request.META['HTTP_USER_AGENT'].find('Googlebot') != -1:
            return HttpResponse('No')
        raise Exception("This is a deliberate error")
