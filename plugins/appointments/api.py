"""
API for appointment data
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response


class AppointmentViewSet(LoginRequiredViewset):
    base_name = 'appointment'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        appointments = patient.appointments.all().order_by('-start_datetime')
        return json_response([a.to_dict() for a in appointments])
