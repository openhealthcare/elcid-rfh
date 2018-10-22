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


class ElcidTemplateView(TemplateView):
    def dispatch(self, *args, **kwargs):
        self.name = kwargs['name']
        return super(ElcidTemplateView, self).dispatch(*args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        return ['elcid/modals/'+self.name]

    def get_context_data(self, *args, **kwargs):
        ctd = super(ElcidTemplateView, self).get_context_data(*args, **kwargs)

        try:
            ctd["model"] = apps.get_model(app_label='elcid', model_name=self.name)
        except LookupError:
            pass

        return ctd
