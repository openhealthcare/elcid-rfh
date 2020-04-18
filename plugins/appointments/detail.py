"""
Custom Detail view for upstream appointment viewing
"""
from opal.core import detail


class AppointmentDetailView(detail.PatientDetailView):
    display_name = "Appointments"
    order        = 10
    template     = "detail/appointment.html"
