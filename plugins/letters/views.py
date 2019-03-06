"""
Views for the letters Opal Plugin
"""
# from django.views.generic import View

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView



class LettersIndexView(LoginRequiredMixin, TemplateView):
    """
    Main entrypoint into the pathway portal service.
    This is the entry point that loads in the pathway.
    """
    template_name = "letters/index.html"