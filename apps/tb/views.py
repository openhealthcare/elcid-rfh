"""
Views for the TB Opal Plugin
"""

from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.tb.models import PatientConsultation

# You might find these helpful !
# from opal.core.views import LoginRequiredMixin, json_response


class ClinicalAdvicePrintView(LoginRequiredMixin, DetailView):
    template_name = 'tb/clinical_advice.html'
    model = PatientConsultation
