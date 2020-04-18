"""
Views for the Appointment plugin
"""
import datetime

from django.views.generic import ListView

from plugins.appointments.models import Appointment


#
# TODO: Reimplement this for TB
#
#
# class ClinicListView(ListView):
#     """
#     Show a list of all future appointments
#     """
#     model         = Appointment
#     template_name = 'appointments/clinic_list.html'

#     def get_queryset(self):
#         return Appointment.objects.filter(
#             start_datetime__gte=datetime.date.today()
#         ).exclude(status_code='Canceled').order_by('start_datetime')
