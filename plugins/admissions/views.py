"""
Views for the Admissions module
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from opal.models import Patient


class UpstreamLocationSnippet(LoginRequiredMixin, DetailView):
    template_name = 'admissions/partials/upstream_location.html'
    model         = Patient
