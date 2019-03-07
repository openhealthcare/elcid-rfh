"""
Views for the letters Opal Plugin
"""
# from django.views.generic import View

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class LettersIndexView(LoginRequiredMixin, TemplateView):
    template_name = "letters/index.html"